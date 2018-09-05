---
title: ffos图形分析之HwcComposer2D
date: 2018-08-08 17:27:10
tags:
---

# HwcCompser2D
HwcComposer2D在firefoxos的图形显示中起一个很重要的作用，与它相关的部分有hwc hal，nsWindow(nsIWidget),nsScreenGonk,FramebufferSurface(DisplaySurface).

HwcCompser2D为gecko提供了一个使用

## HwcCompser2D.h
 HwcCompser2D为gecko提供了一种使用AOSP HAL中的hwcomposer.h来渲染frame的方法。

hwcomposer.h为display compostion的专用硬件定义了相应的接口。该硬件通常比gpu更快，更有效率。相应的，作为代价，某些通常的特性只能被牺牲了：没有3d变换，没有中间曲面，没有特殊的着色器效果，并且还会缺少一些依赖平台的特殊优化。

通常来讲，当弃用hwc时，gecko会先尝试用HwcCompser2D来compose frame。如果HwcCompser2D没法合成frame，那么它就会退回去使用opengl（带gpu）来合成。

```
class HwcComposer2D : public mozilla::layers::Composer2D {
public:
    HwcComposer2D();
    virtual ~HwcComposer2D();

    static HwcComposer2D* GetInstance();

    // Returns TRUE if the container has been succesfully rendered
    // Returns FALSE if the container cannot be fully rendered
    // by this composer so nothing was rendered at all
    virtual bool TryRenderWithHwc(layers::Layer* aRoot,
                                  nsIWidget* aWidget,
                                  bool aGeometryChanged) override;

    virtual bool Render(nsIWidget* aWidget) override;

    virtual bool HasHwc() override { return mHal->HasHwc(); }

    bool EnableVsync(bool aEnable);
    bool RegisterHwcEventCallback();
    void Vsync(int aDisplay, int64_t aTimestamp);
    void Invalidate();
    void Hotplug(int aDisplay, int aConnected);
    void SetCompositorParent(layers::CompositorParent* aCompositorParent);
```