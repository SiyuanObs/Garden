from garden.models import GameState
from garden.ui import run_app


def main() -> None:
    state = GameState()
    run_app(state)


if __name__ == "__main__":
    main()
