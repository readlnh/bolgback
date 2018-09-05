---
title: firefox os图形探索之CompositorOGL
date: 2018-08-09 15:40:41
tags:
---

Firefox OS里有两种compositor
- CompositorOGL
- BasicCompositor

其中CompositorOGL使用OpenGL来Compositing，在gonk上Firefox OS默认就是用它。

# CompositorOGL
使用OpenGL来Compositing。它的compositing过程由LayerManagerComposite来控制。`BeginFrame()`启动一个新的帧合成，`EndFrame()`将当前帧刷新到屏幕并整理。

## CompositorOGL.h

### class CompositorTexturePoolOGL
compositor的临时纹理池(pools of temporary gl textures)接口.
textures完全属于pool，所以后者应当负责调用`fDelete Textures`。
GetTexture的用户接收仅在当前帧的持续时间内有效的纹理。
这主要用于需要将共享对象（例如EGLImage）附加到gl纹理的直接纹理API。


```c++
class CompositorTexturePoolOGL
{
protected:
  virtual ~CompositorTexturePoolOGL() {}

public:
  NS_INLINE_DECL_REFCOUNTING(CompositorTexturePoolOGL)

  virtual void Clear() = 0;

  virtual GLuint GetTexture(GLenum aTarget, GLenum aEnum) = 0;

  virtual void EndFrame() = 0;
};
```

#  PerUnitTexturePoolOGL
```c++
class PerUnitTexturePoolOGL : public CompositorTexturePoolOGL
```
积极地重用纹理。每个纹理单元总共一个gl纹理。
到目前为止，这还没有在b2g上显示出最好的结果。

# PerFrameTexturePoolOGL
和上面类似，这里是每帧了
重用纹理池中在当前frame尚没有被使用的gl texures。
所有在end of frame还没有被使用的textures都会被删除。
```c++
class PerFrameTexturePoolOGL : public CompositorTexturePoolOGL
```



























开机动画相关gecko/widget/gonk/libdisplay/BootAnimation.cpp
