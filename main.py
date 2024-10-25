import asyncio
import sys

import players
from src import ladder, team_stats
from src.tools import File, logger, load_env, save_to_json


def parse_args(args: list[str]) -> str:
    default_msg = (
        "USAGE: python main.py <arg>\narg options: ladder, players, team_stats"
    )
    num_args: int = len(args)

    if num_args == 1 or num_args >= 3:
        sys.exit(default_msg)

    elif sys.argv[1] not in {"ladder", "players", "team_stats"}:
        sys.exit(default_msg)

    return sys.argv[1]


async def main():
    arg: str = parse_args(sys.argv)
    env: dict = load_env(File.path("env.toml"))
    
    if arg == "ladder":
        data = ladder.get(env)
    
    elif arg == "team_stats":
        data = await team_stats.get(env)
    
    elif arg == "players":
        data = await players.get(env)
    
    # Output to file
    if data:
        route: str = File.path("data")
        filename: str = env[arg]["filename"]
        save_to_json(data, route, filename)
    else:
        sys.exit("No data found. Program Terminated.")


if __name__ == "__main__":
    logger(File.path("data/app.log"))
    asyncio.run(main())
