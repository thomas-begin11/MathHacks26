"""Widget construction for Road Trip: Function Junction.

Visual controls live here so game rules in main.py stay focused on gameplay.
"""


def create_game_ui(Page, UI, Theme, width, height, graph_top, graph_bottom):
    """Create and style the game-screen controls."""
    Page.Open("Game")
    top = UI.Frame(0, 0, width, graph_top)
    top.bg = "dark"
    title = UI.Text("", 16, 11, 26)
    title.color = "white"
    readout = UI.Text("", 520, 16, 20)
    readout.color = "#ffd25a"
    menu_btn = UI.Button("Menu", 840, 8, 110, 34)
    fullscreen_btn = UI.Button("Fullscreen", 710, 8, 120, 34)

    bottom = UI.Frame(0, graph_bottom, width, height - graph_bottom)
    bottom.bg = "panel"
    msg = UI.Text("", 16, 468, 18)
    ylab = UI.Text("y =", 16, 499, 26)
    ylab.color = "white"
    inp = UI.Input("type a function, e.g. 0.3x + 1", 62, 494, 480, 38)
    drive_btn = UI.Button("Drive!", 556, 494, 120, 38)
    reset_btn = UI.Button("Reset", 686, 494, 100, 38)
    next_btn = UI.Button("Next level", 796, 494, 148, 38)
    next_btn.visible = False
    Theme.Set("modern")
    for button, color in ((menu_btn, "#495057"), (drive_btn, "#2f9e44"),
                          (reset_btn, "#868e96"), (next_btn, "#1971c2")):
        button.bg = color
        button.color = "white"
    return locals()


def create_menu(Page, UI, levels, on_level_selected):
    """Create the level-selection page and attach its callbacks."""
    Page.Open("Menu")
    UI.Text("Road Trip", 300, 50, 72).color = "#ffd25a"
    UI.Text("Function Junction", 330, 130, 36).color = "white"
    UI.Text("Drive the car to the flag by writing the road as a function, y = f(x).", 190, 190, 20).color = "#cfd8e3"
    for i, level in enumerate(levels):
        button = UI.Button(level["name"] + "  -  " + level["concept"], 250, 250 + i * 62, 460, 50)
        button.bg = "#1971c2"
        button.color = "white"
        button.on_click = (lambda number: lambda: on_level_selected(number))(i)
