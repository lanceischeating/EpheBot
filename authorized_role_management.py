import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUTHORIZED_ROLES_DIR = os.path.join(BASE_DIR, "GuildRoles")

if not os.path.isdir(AUTHORIZED_ROLES_DIR):
    os.makedirs(AUTHORIZED_ROLES_DIR)

AUTH_FILE = os.path.join(AUTHORIZED_ROLES_DIR, "auth_roles.txt")


def load_auth_roles() -> dict:
    """
    Reads the authorized_roles.txt file and returns a dictionary
    mapping guild IDs to lists of authorized role IDs.
    Expected file format per line: guild_id: role_id1, role_id2, ...
    """
    data = {}
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    guild_str, role_str = line.split(":", 1)
                    guild_id = int(guild_str.strip())
                    roles = [int(role.strip()) for role in role_str.split(",") if role.strip()]
                    data[guild_id] = roles
                except Exception as e:
                    print(f"Error loading authorized roles: {line} {e}")
    return data


def save_auth_roles(data) -> None:
    """
    Saves the authorized roles dictionary to AUTH_FILE.
    """
    with open(AUTH_FILE, "w", encoding="utf-8") as f:
        for guild_id, roles, in data.items():
            line = f"{guild_id}: {', '.join(map(str, roles))}\n"
            f.write(line)
