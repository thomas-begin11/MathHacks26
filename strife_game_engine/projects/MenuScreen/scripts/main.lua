Page.Open("main")
local title = UI.Text("Strife!", 370, -30, 45)
Tween(title, "y", 120, 0.6)
title.color = "#000000"
title.z = 4

local sTitle = UI.Text("Lite", 510, 170, 22)
sTitle.z = 4
sTitle.color = "#000000"
sTitle.alpha = 0


local bg2 = UI.Image("backdrop.png", 250, -20, .7)
--Buttonid = go next  
After(0.6, function()               
  Tween(sTitle, "alpha", 1, 1)       
end)

function on_update(dt)
-- logic goes here
end
