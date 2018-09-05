---
title: firefoxos图形自顶向下研究1
date: 2018-07-31 15:26:23
tags:
---

工作需要开始研究firefoxos的图形相关的代码，资料非常少，姑且做的记录备忘

# nsDisplayList.h

## nsDisplayListBuilder
首先从nsDisplayListBuilder入手。
nsDisplayListBuilder创建了nsDisplayList并且创建了nsIFrame，这部分相关的代码位于/gecko/layout/base/nsDisplayList.h中。发现代码开头的注释

```c++
/*
 * structures that represent things to be painted (ordered in z-order),
 * used during painting and hit testing
 */
```
可见该文件定义的是在绘制和hit测试中会用到的要绘制的内容(根据z-order)的结构

```
/*一组混合模式，从不包含OP_OVER（因为它被认为是默认值，而不是特定的混合模式）。*/
// A set of blend modes, that never includes OP_OVER (since it's
// considered the default, rather than a specific blend mode).
typedef mozilla::EnumSet<mozilla::gfx::CompositionOp> BlendModeSet;

```

一个nsIFrame可以有很多不同的可视部分组成。例如，一个图像帧可以由背景，边框，轮廓，边框，图像本身和一个半透明的可选单叠加而成。通常，这些部分可以在不连续的z水平上被绘制出来。可以参照[ http://www.w3.org/TR/CSS21/zindex.html]( http://www.w3.org/TR/CSS21/zindex.html) 

我们为frame tree构造了一个display list使得每个可视元素都有相应的一个item。display list本身也是树形结构因此某些item同时也包含一些别的item;然而，它的结构和它的源frame tree的结构并不一致。display list的item是按z-order排序的。一个display list可以用来绘制frames，决定哪一帧是鼠标事件的目标target，决定哪一帧在屏幕滚动时需要重绘。为不同任务创建的display list在效率上可能也完全不同;特别的，有些frames仅仅需要包含事件处理的item 的display list，（通常来说）display list在绘制时不需要包含这些items。举例来说，对于不显示看得到的背景的的frames我们会避免在绘制时创建nsPlayBackground items。但是对于事件处理我们会需要这些背景，因为它们对事件是非透明的。

我们可以通过巧妙地多次遍历帧树来避免构造显式显示列表。然而，具体化(reifying)display list，降低代码复杂度，减少每一帧需要遍历的次数看起来才是更好的做法，这样做也意味着我们可以共享绘画，事件处理和（屏幕）滚动分析的代码。

display list的生命周期很短，content和frame trees在一个display list创建和销毁的期间是不可改变的。display list在reflow期间是不能被创建的，因为这样可能导致frame tree处于前后不一致的状态（例如，帧的存储溢出区域可能不包括其所有子节点的边界）。但是在reflow开始前或者处于挂起状态下创建display list应该是没问题的。

一个display list包含了“扩展的”frame tree;一棵frame tree的display list包含包括来自子文档的帧的FRAME / IFRAME元素。

display item的坐标和离它们最近的参考frame ancestor（祖先）有关。display root和任何具有变换的帧都充当它们的frame subtree 的参考frame。

继续看代码

```c++
// All types are defined in nsDisplayItemTypes.h
//所有的类定都被定义在nsDisplayItemTypes.h里
#define NS_DISPLAY_DECL_NAME(n, e) \
  virtual const char* Name() override { return n; } \
  virtual Type GetType() override { return e; }
```
我们来看nsDisplayListBuilder

```c++
class nsDisplayListBuilder {
public:
  typedef mozilla::FramePropertyDescriptor FramePropertyDescriptor;
  typedef mozilla::FrameLayerBuilder FrameLayerBuilder;
  typedef mozilla::DisplayItemClip DisplayItemClip;
  typedef mozilla::DisplayListClipState DisplayListClipState;
  typedef nsIWidget::ThemeGeometry ThemeGeometry;
  typedef mozilla::layers::Layer Layer;
  typedef mozilla::layers::FrameMetrics FrameMetrics;
  typedef mozilla::layers::FrameMetrics::ViewID ViewID;
  ...
  }
```
nsDisplayListBuilder管理了一个display list，并将其作为参数传给nsIFrame::BuildDisplayList。它包含不会逐帧更改的参数，并使用PLArena管理显display list memory。它还为所有display list items建立参考坐标系。某些参数可从prescontext / presshell获得，但为了更快/更方便的访问我们通常把它们复制到构造器(builder)中。

```c++
/**
   * @param aReferenceFrame the frame at the root of the subtree; its origin
   * is the origin of the reference coordinate system for this display list
   * @param aMode encodes what the builder is being used for.
   * @param aBuildCaret whether or not we should include the caret in any
   * display lists that we make.
   */
  enum Mode {
    PAINTING,
    EVENT_DELIVERY,
    PLUGIN_GEOMETRY,
    IMAGE_VISIBILITY,
    OTHER
  };
  nsDisplayListBuilder(nsIFrame* aReferenceFrame, Mode aMode, bool aBuildCaret);
  ~nsDisplayListBuilder();
```
我们来看构造函数，根据注释
- 参数`aReferenceFrame` 子树的根的frame，其原点是display list参考坐标系的原点
- 参数`aMode` 构造器正在使用的编码模式
- 参数 `aBuildCaret` 是否应该在display list中包含我们制作的插入符号
之后的一些都是builder的各种操作，暂且不表

##  nsDisplayItemLink 
```c++
class nsDisplayItem;
class nsDisplayList;
/**
 * nsDisplayItems are put in singly-linked lists rooted in an nsDisplayList.
 * nsDisplayItemLink holds the link. The lists are linked from lowest to
 * highest in z-order.
 */
class nsDisplayItemLink {
  // This is never instantiated directly, so no need to count constructors and
  // destructors.
protected:
  nsDisplayItemLink() : mAbove(nullptr) {}
  nsDisplayItem* mAbove;  
  
  friend class nsDisplayList;
};
```
nsDisplayItems放在以nsDisplayList为基础的单链表中,nsDisplayItem Link保存链接。列表按z-order从最低到最高链接。由于不会直接被引用，所以改类也不需要构造和析构函数。

## nsDisplayItem
``` c++
class nsDisplayItem : public nsDisplayItemLink {
public: ...
#ifdef MOZ_DUMP_PAINTING ...
#endif ...
 // Contains all the type integers for each display list item type
#include "nsDisplayItemTypes.h" ...
#ifdef MOZ_DUMP_PAINTING
  /**
   * Mark this display item as being painted via FrameLayerBuilder::DrawPaintedLayer.
   */
  bool Painted() { return mPainted; }

  /** ...
   * Check if this display item has been painted.
   */
  void SetPainted() { mPainted = true; }
#endif ...
protected: ...
 #ifdef MOZ_DUMP_PAINTING
  // True if this frame has been painted.
  bool      mPainted;
#endif
};
```
nsDisplayitem是渲染(rendering)和事件测试(event testing)的基本单元(unit)。这个类的每个实例表示可以在屏幕上绘制的实体。例如，一个frame的CSS背景，或一个frame的文本字符串。

nsDisplayItems可以是容器---也就是说，它们可以通过递归遍历子项列表来执行测试和绘画。

这些(DispalyItems)是在display list构造时分配的arena。一个典型的子类只有一个frame指针，所它的对象只有三个指针(vtable, next-item, frame)

display items始终属于一个list(暂时从一个list移动到另一个list除外)

## nsDisplayList
``` c++
class nsDisplayList {
public:
  typedef mozilla::layers::Layer Layer;
  typedef mozilla::layers::LayerManager LayerManager;
  typedef mozilla::layers::PaintedLayer PaintedLayer;

  /**
   * Create an empty list.
   */
  nsDisplayList()
    : mIsOpaque(false)
    , mForceTransparentSurface(false)
  {
    mTop = &mSentinel;
    mSentinel.mAbove = nullptr;
  }
  ~nsDisplayList() {
    if (mSentinel.mAbove) {
      NS_WARNING("Nonempty list left over?");
    }
    DeleteAll();
  }
  ...
  private: ...
};
```
管理一个单链接的display list的列表

mSentinel是标记列表值，是以null结尾的链接项列表中的第一个值。 mTop是列表中的最后一项（其'above'指针为null）。该类没有虚拟方法，所以列表对象只是两个指针。

向上遍历这个list很快，而向下遍历则很慢，所以我们不支持向下遍历。向下遍历的方法`(HitTest(), ComputeVisibility())` 会在items向下遍历时内部临时构建一个内部数组，因此总体而言它们仍然是线性时间复杂度。我们针对items和lists对`AppendToTop()`进行了优化，并且代码量很小。`AppendToBottom()`效率也很不错。

## nsDisplayListSet
```c++
class nsDisplayListSet {
public:
  /**
   * @return a list where one should place the border and/or background for
   * this frame (everything from steps 1 and 2 of CSS 2.1 appendix E)
   */
  nsDisplayList* BorderBackground() const { return mBorderBackground; }
  /**
   * @return a list where one should place the borders and/or backgrounds for
   * block-level in-flow descendants (step 4 of CSS 2.1 appendix E)
   */
  nsDisplayList* BlockBorderBackgrounds() const { return mBlockBorderBackgrounds; }
  /**
   * @return a list where one should place descendant floats (step 5 of
   * CSS 2.1 appendix E)
   */
  nsDisplayList* Floats() const { return mFloats; }
  /**
   * @return a list where one should place the (pseudo) stacking contexts 
   * for descendants of this frame (everything from steps 3, 7 and 8
   * of CSS 2.1 appendix E)
   */
  nsDisplayList* PositionedDescendants() const { return mPositioned; }
  /**
   * @return a list where one should place the outlines
   * for this frame and its descendants (step 9 of CSS 2.1 appendix E)
   */
  nsDisplayList* Outlines() const { return mOutlines; }
  /**
   * @return a list where one should place all other content
   */
  nsDisplayList* Content() const { return mContent; }
  
  nsDisplayListSet(nsDisplayList* aBorderBackground,
                   nsDisplayList* aBlockBorderBackgrounds,
                   nsDisplayList* aFloats,
                   nsDisplayList* aContent,
                   nsDisplayList* aPositionedDescendants,
                   nsDisplayList* aOutlines) :
     mBorderBackground(aBorderBackground),
     mBlockBorderBackgrounds(aBlockBorderBackgrounds),
     mFloats(aFloats),
     mContent(aContent),
     mPositioned(aPositionedDescendants),
     mOutlines(aOutlines) {
  }

  /**
   * A copy constructor that lets the caller override the BorderBackground
   * list.
   */  
  nsDisplayListSet(const nsDisplayListSet& aLists,
                   nsDisplayList* aBorderBackground) :
     mBorderBackground(aBorderBackground),
     mBlockBorderBackgrounds(aLists.BlockBorderBackgrounds()),
     mFloats(aLists.Floats()),
     mContent(aLists.Content()),
     mPositioned(aLists.PositionedDescendants()),
     mOutlines(aLists.Outlines()) {
  }
  
  /**
   * Move all display items in our lists to top of the corresponding lists in the
   * destination.
   */
  void MoveTo(const nsDisplayListSet& aDestination) const;
  
  private: ...
  protected: ...
```
这个类实际上就是一个display list的集合了。它会被作为参数传到nsIFrame::BuildDisplayList中。这个method会把生成的所有items放到此处给出的相应的list里。这个类基本上可以说是每个独立的stacking layer的collection。

lists本身是objects(对象)的external(扩展)，因此实际上可以共享。有些list的指针甚至对应的是同一个list。

## nsDisplayListCollection
```c++
struct nsDisplayListCollection : public nsDisplayListSet { ...
private: ...
};
```
nsDisplayListSet的一个特化，其中列表实际上是对象的内部，并且都是不同的。

## nsDisplayItem的各种子类
`nsDisplayItem`有各种子类，比如
- `nsDisplayImageContainer`
-  `nsDisplayGeneric`
- `nsDisplayGenericOverflow`
- `nsDisplayCaret`
- `nsDisplayBorder`
- `nsDisplaySolidColorBase`
-  ...

这些不同类型的display item代表了显示时不同的元素。




















