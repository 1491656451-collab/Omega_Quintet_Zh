# -*- coding: utf-8 -*-
"""grSystemWorld.dds（世界地图）19 个框。按钮底板里的字用 chroma 模式抠。"""
C = lambda t: {"chroma": t}
M = {
  0: None, 1: None, 2: None, 3: None,          # 宝石图标
  4: None,            # NEW（保留）
  5: C("已完成"),      # Completed
  6: C("未接受"),      # Unassigned
  7: C("进行中"),      # In Progress
  8: None, 9: None, 10: None,                  # 图标 / 光条
  11: None,           # New（保留）
  12: C("对话"),       # Talk
  13: C("事件"),       # Event
  14: C("委托"),       # Quest
  15: None, 16: None, 17: None,
  18: {"chroma": 1, "parts": ["", "事件", "", "事件", "", "事件", "", "事件", "", "事件"]},
}
