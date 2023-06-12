import mesa
import copy
import pygraphviz as pgv

from mesa.visualization.UserParam import UserSettableParameter


BROWN = "Brown"
BLUE = "Blue"
ALL = "All"


class Islander(mesa.Agent):
    """Islander with blue or brown eyes"""

    # Initialize islander with eye color
    def __init__(self, unique_id, model, eye_color):
        super().__init__(unique_id, model)
        self.eye_color = eye_color
        self.alive = True

    # Update knowledge to determine own eye color
    def determine_eye_color(self) -> str | None:
        return None

    # Agent step function called by mesa
    def step(self):
        if self.eye_color == BLUE:
            self.alive = (self.determine_eye_color() == None)


class IslandModel(mesa.Model):
    """Keeps track of islanders and Kripke models"""

    # Initialize island grid with islanders
    def __init__(self, n_brown, n_blue, width, height, variant):
        assert (n_brown + n_blue) <= (width * height), \
                f"Grid of size {width}x{height} is too small for {n_brown + n_blue} agents"
        self.n_brown = n_brown
        self.n_blue = n_blue
        self.num_agents = n_brown + n_blue
        self.agents = []
        self.variant = variant
        self.grid = mesa.space.SingleGrid(width, height, True)
        self.schedule = mesa.time.SimultaneousActivation(self)
        self.data_alive = mesa.DataCollector({ALL: lambda m: m.get_alive(), 
                                              BROWN: lambda m: m.get_alive_brown(), 
                                              BLUE: lambda m: m.get_alive_blue(),
                                            })
        self.data_alive.collect(self)

        # Create agents
        for i in range(self.num_agents):
            eye_color = BLUE
            if i < n_brown:
                eye_color = BROWN

            a = Islander(i, self, eye_color)
            self.agents.append(a)
            self.schedule.add(a)
            x = (i) % width
            y = (i) // width
            self.grid.place_agent(a, (x, y))

        # Create Kripke models
        brown_eyed = [BROWN] * n_brown
        blue_eyed = [BLUE] * n_blue

        w_real = brown_eyed + blue_eyed
        w_possible = []
        for idx, color in enumerate(w_real):
            w_new = copy.copy(w_real)
            w_new[idx] = flip_eye_color(color)
            w_possible.append(w_new)
        w_all = [w_real, *w_possible]

    # Number of living agents
    def get_alive(self):
        return sum([1 for a in self.agents if a.alive])

    # Number of living agents with brown eyes
    def get_alive_brown(self):
        return sum([1 for a in self.agents if (a.alive and a.eye_color == BROWN)])

    # Number of living agents with blue eyes
    def get_alive_blue(self):
        return sum([1 for a in self.agents if (a.alive and a.eye_color == BLUE)])

    # Model step function called by mesa
    def step(self):
        self.schedule.step()
        self.data_alive.collect(self)


# Specifiy how agents are drawn on the grid
def agent_portrayal(agent):
    portrayal = {
        "Shape": "circle",
        "Filled": agent.alive,
        "Layer": 0,
        "Color": agent.eye_color.lower(),
        "r": 0.5,
    }
    return portrayal

# Flip blue <-> brown
def flip_eye_color(c):
    return BLUE if c == BROWN else BROWN


# Create model & launch server
if __name__ == "__main__":
    grid = mesa.visualization.CanvasGrid(agent_portrayal, 10, 10, 500, 500)
    chart = mesa.visualization.ChartModule([{"Label": ALL, "Color": "Black"}, 
                                            {"Label": BROWN, "Color": BROWN},
                                            {"Label": BLUE, "Color": BLUE},
                                            ], 
                                        data_collector_name="data_alive",
                                        )

    model_params = {
        "width": 10,
        "height": 10,
        "n_brown": UserSettableParameter("slider", "Brown-eyed islanders", 90, 0, 90, 1),
        "n_blue": UserSettableParameter("slider", "Blue-eyed islanders", 10, 0, 10, 1),
        "variant": UserSettableParameter("choice", "Puzzle Variant", value="Default",
                                          choices=["Default", "v1", "v2", "v3"])
    }

    server = mesa.visualization.ModularServer(
        IslandModel, [grid, chart], "Island Model", model_params)
    server.port = 8521  # The default
    server.launch()
