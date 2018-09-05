---
title: firefoxos图形总体框架
date: 2018-08-01 10:59:25
tags:
---

# Layout和Graphics之间的界限
- nsDisplayListBuilder
	- 管理一个display list
	- 包含不是逐帧变换的参数
	- nsIFrame有很多不同的可视元素。为frame tree构造了一个display list使得每一个可视元素都有一个对应的item
	- display list可以提高效率而不是直接遍历frame tree	
	
- nsDisplayList
	- 管理一个单链接的display list
	- display list items按z-order排序
	- 一个display list可以用来绘制frames，决定哪一帧是鼠标事件的目标target，决定哪一帧在屏幕滚动时需要重绘
	- 角色和 'scene graph'相类似

- nsDisplayItem
	-  rendering和event testing的最小单元(unit)
	- 每个实例代表一个可以在屏幕上绘制的实体e.g., frame的CSS background, 或frame的text string