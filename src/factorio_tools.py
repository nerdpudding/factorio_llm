"""
High-level Factorio tools for LLM integration.

Provides easy-to-use methods for querying and controlling Factorio.
"""

from typing import Optional
from dataclasses import dataclass

from .rcon_wrapper import RCONWrapper, RCONError


@dataclass
class GameInfo:
    """Basic game information."""
    tick: int
    surface_name: str
    player_count: int
    version: str


@dataclass
class EntityInfo:
    """Information about an entity."""
    name: str
    position_x: float
    position_y: float


@dataclass
class ProductionStats:
    """Production statistics for an item."""
    item: str
    input_count: int   # produced (items entering the system)
    output_count: int  # consumed (items leaving the system)


@dataclass
class Position:
    """A position in the game world."""
    x: float
    y: float


@dataclass
class ResourcePatch:
    """Information about a resource patch."""
    name: str
    position_x: float
    position_y: float
    amount: int


@dataclass
class InventoryItem:
    """An item in an inventory."""
    name: str
    count: int


class FactorioTools:
    """
    High-level tools for interacting with Factorio.

    Usage:
        tools = FactorioTools()
        tools.connect()

        info = tools.get_game_info()
        print(f"Game tick: {info.tick}")

        trees = tools.count_entities("tree")
        print(f"Trees on map: {trees}")

        tools.disconnect()

    Or as context manager:
        with FactorioTools() as tools:
            print(tools.get_tick())
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 27015,
        password: str = "test123"
    ):
        self._rcon = RCONWrapper(host, port, password)

    def connect(self) -> None:
        """Connect to Factorio server."""
        self._rcon.connect()

    def disconnect(self) -> None:
        """Disconnect from server."""
        self._rcon.disconnect()

    def reconnect(self, max_attempts: int = 3, delay: float = 2.0) -> bool:
        """
        Try to reconnect to the server.

        Args:
            max_attempts: Maximum reconnection attempts
            delay: Delay between attempts in seconds

        Returns:
            True if reconnected, False otherwise
        """
        import time

        for attempt in range(max_attempts):
            try:
                self._rcon.disconnect()
                time.sleep(delay)
                self._rcon.connect()
                return True
            except Exception:
                if attempt < max_attempts - 1:
                    continue
        return False

    @property
    def connected(self) -> bool:
        """Check if connected."""
        return self._rcon.connected

    # -------------------------------------------------------------------------
    # Basic Queries
    # -------------------------------------------------------------------------

    def get_tick(self) -> int:
        """Get current game tick."""
        result = self._rcon.query_lua("game.tick")
        return int(result) if result else 0

    def get_version(self) -> str:
        """Get Factorio version."""
        result = self._rcon.send_command("/version")
        return result.strip() if result else "unknown"

    def get_game_info(self) -> GameInfo:
        """Get basic game information."""
        tick = self.get_tick()
        version = self.get_version()

        # Get surface name (main surface is usually "nauvis")
        surface_name = self._rcon.query_lua('game.surfaces[1].name') or "unknown"

        # Get player count
        player_count_str = self._rcon.query_lua('#game.players') or "0"
        player_count = int(player_count_str)

        return GameInfo(
            tick=tick,
            surface_name=surface_name,
            player_count=player_count,
            version=version
        )

    # -------------------------------------------------------------------------
    # Entity Queries
    # -------------------------------------------------------------------------

    def count_entities(self, entity_type: str) -> int:
        """
        Count entities on the main surface.

        Searches by name first, then by type if no results.
        This handles both specific items (wooden-chest) and categories (tree).

        Args:
            entity_type: Entity name or type (e.g., "wooden-chest", "tree", "iron-ore")

        Returns:
            Number of entities found.
        """
        # Try by name first (e.g., "wooden-chest", "iron-ore")
        lua_name = f'#game.surfaces[1].find_entities_filtered{{name="{entity_type}"}}'
        result = self._rcon.query_lua(lua_name)
        count = int(result) if result else 0

        if count > 0:
            return count

        # If no results, try by type (e.g., "tree", "container")
        lua_type = f'#game.surfaces[1].find_entities_filtered{{type="{entity_type}"}}'
        result = self._rcon.query_lua(lua_type)
        return int(result) if result else 0

    def count_entities_by_name(self, entity_name: str) -> int:
        """
        Count entities with a specific name.

        Args:
            entity_name: Entity name (e.g., "iron-chest", "transport-belt")

        Returns:
            Number of entities found.
        """
        lua = f'#game.surfaces[1].find_entities_filtered{{name="{entity_name}"}}'
        result = self._rcon.query_lua(lua)
        return int(result) if result else 0

    def list_entities(
        self,
        entity_type: str,
        limit: int = 10
    ) -> list[EntityInfo]:
        """
        List entities of a given type with their positions.

        Args:
            entity_type: Entity type to search for.
            limit: Maximum number of entities to return.

        Returns:
            List of EntityInfo objects.
        """
        # Build Lua that returns a table of {name, x, y} for each entity
        lua = f'''
(function()
    local entities = game.surfaces[1].find_entities_filtered{{type="{entity_type}"}}
    local result = {{}}
    local count = 0
    for _, e in pairs(entities) do
        if count >= {limit} then break end
        table.insert(result, {{name=e.name, x=e.position.x, y=e.position.y}})
        count = count + 1
    end
    return result
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return []

        return self._parse_entity_list(result)

    def _parse_entity_list(self, serpent_output: str) -> list[EntityInfo]:
        """Parse serpent.line output of entity list."""
        entities = []
        import re

        # Handle spaces and different field orders
        blocks = re.findall(r'\{[^}]+\}', serpent_output)

        for block in blocks:
            name_match = re.search(r'name\s*=\s*"([^"]+)"', block)
            x_match = re.search(r'x\s*=\s*([-\d.]+)', block)
            y_match = re.search(r'y\s*=\s*([-\d.]+)', block)

            if name_match and x_match and y_match:
                entities.append(EntityInfo(
                    name=name_match.group(1),
                    position_x=float(x_match.group(1)),
                    position_y=float(y_match.group(1))
                ))

        return entities

    # -------------------------------------------------------------------------
    # Production Statistics (Factorio 2.0 API)
    # IMPORTANT: Use DOT syntax (.) not COLON syntax (:)
    # Colon adds 'self' as first arg causing "Invalid SurfaceIdentification"
    # -------------------------------------------------------------------------

    def get_production_stats(self, item: str, surface: str = "nauvis") -> ProductionStats:
        """
        Get production statistics for an item.

        Args:
            item: Item name (e.g., "iron-plate", "copper-cable", "coal")
            surface: Surface name (default "nauvis")

        Returns:
            ProductionStats with input_count (produced) and output_count (consumed)
        """
        # Use DOT syntax - colon passes force as implicit first arg which breaks it
        input_lua = f'game.forces["player"].get_item_production_statistics("{surface}").get_input_count("{item}")'
        output_lua = f'game.forces["player"].get_item_production_statistics("{surface}").get_output_count("{item}")'

        input_result = self._rcon.query_lua(input_lua)
        output_result = self._rcon.query_lua(output_lua)

        return ProductionStats(
            item=item,
            input_count=int(input_result) if input_result else 0,
            output_count=int(output_result) if output_result else 0
        )

    # -------------------------------------------------------------------------
    # Phase 2: Player & Position
    # -------------------------------------------------------------------------

    def get_player_position(self) -> Position:
        """
        Get the first connected player's position.

        Returns:
            Position with x, y coordinates.
        """
        lua = 'game.connected_players[1].position'
        result = self._rcon.query_lua_table(lua)

        if not result:
            return Position(x=0, y=0)

        # Parse serpent output: {x = 123.5, y = -45.2} (note: spaces around =)
        import re
        match = re.search(r'x\s*=\s*([-\d.]+).*y\s*=\s*([-\d.]+)', result)
        if match:
            return Position(x=float(match.group(1)), y=float(match.group(2)))
        return Position(x=0, y=0)

    def find_nearby_entities(self, radius: float = 20) -> list[dict]:
        """
        Find all entities near the player (buildings, chests, machines, etc.).

        Args:
            radius: Search radius around player (default 20 tiles)

        Returns:
            List of dicts with name, type, position, and count grouped by location.
        """
        lua = f'''
(function()
    local p = game.connected_players[1]
    local pos = p.position
    local area = {{{{pos.x - {radius}, pos.y - {radius}}}, {{pos.x + {radius}, pos.y + {radius}}}}}
    local entities = p.surface.find_entities_filtered{{area=area}}
    local result = {{}}
    local count = 0
    for _, e in pairs(entities) do
        if e.name ~= "character" and e.type ~= "resource" and e.type ~= "tree" and e.type ~= "fish" then
            if count < 30 then
                table.insert(result, {{name=e.name, type=e.type, x=e.position.x, y=e.position.y}})
                count = count + 1
            end
        end
    end
    return result
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return []

        return self._parse_nearby_entities(result)

    def _parse_nearby_entities(self, serpent_output: str) -> list[dict]:
        """Parse serpent output of nearby entities."""
        import re
        entities = []

        blocks = re.findall(r'\{[^}]+\}', serpent_output)

        for block in blocks:
            name_match = re.search(r'name\s*=\s*"([^"]+)"', block)
            type_match = re.search(r'type\s*=\s*"([^"]+)"', block)
            x_match = re.search(r'x\s*=\s*([-\d.]+)', block)
            y_match = re.search(r'y\s*=\s*([-\d.]+)', block)

            if name_match and x_match and y_match:
                entities.append({
                    "name": name_match.group(1),
                    "type": type_match.group(1) if type_match else "unknown",
                    "x": round(float(x_match.group(1)), 1),
                    "y": round(float(y_match.group(1)), 1)
                })

        return entities

    def find_nearby_resources(self, radius: float = 50) -> list[dict]:
        """
        Find resource patches near the player and return TOTAL amounts.

        Args:
            radius: Search radius around player (default 50 tiles)

        Returns:
            List of dicts with resource name, total amount, tile count, and center position.
        """
        lua = f'''
(function()
    local p = game.connected_players[1]
    local pos = p.position
    local area = {{{{pos.x - {radius}, pos.y - {radius}}}, {{pos.x + {radius}, pos.y + {radius}}}}}
    local resources = p.surface.find_entities_filtered{{area=area, type="resource"}}
    local totals = {{}}
    for _, r in pairs(resources) do
        if not totals[r.name] then
            totals[r.name] = {{total=0, tiles=0, sum_x=0, sum_y=0}}
        end
        totals[r.name].total = totals[r.name].total + r.amount
        totals[r.name].tiles = totals[r.name].tiles + 1
        totals[r.name].sum_x = totals[r.name].sum_x + r.position.x
        totals[r.name].sum_y = totals[r.name].sum_y + r.position.y
    end
    local result = {{}}
    for name, data in pairs(totals) do
        table.insert(result, {{
            name=name,
            total_amount=data.total,
            tile_count=data.tiles,
            center_x=data.sum_x/data.tiles,
            center_y=data.sum_y/data.tiles
        }})
    end
    return result
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return []

        return self._parse_resource_totals(result)

    def _parse_resource_totals(self, serpent_output: str) -> list[dict]:
        """Parse serpent output of resource totals."""
        import re
        resources = []

        blocks = re.findall(r'\{[^}]+\}', serpent_output)
        for block in blocks:
            name_match = re.search(r'name\s*=\s*"([^"]+)"', block)
            total_match = re.search(r'total_amount\s*=\s*(\d+)', block)
            tiles_match = re.search(r'tile_count\s*=\s*(\d+)', block)
            cx_match = re.search(r'center_x\s*=\s*([-\d.]+)', block)
            cy_match = re.search(r'center_y\s*=\s*([-\d.]+)', block)

            if name_match and total_match:
                resources.append({
                    "name": name_match.group(1),
                    "total_amount": int(total_match.group(1)),
                    "tile_count": int(tiles_match.group(1)) if tiles_match else 0,
                    "center_x": round(float(cx_match.group(1)), 1) if cx_match else 0,
                    "center_y": round(float(cy_match.group(1)), 1) if cy_match else 0
                })

        # Sort by total amount descending
        resources.sort(key=lambda x: x["total_amount"], reverse=True)
        return resources

    def _parse_resource_list(self, serpent_output: str) -> list[ResourcePatch]:
        """Parse serpent output of resource list."""
        import re
        resources = []

        # Pattern handles spaces: {name = "iron-ore", x = 123, y = 456, amount = 1000}
        # Also handles different field orders by searching for each field separately
        blocks = re.findall(r'\{[^}]+\}', serpent_output)

        for block in blocks:
            name_match = re.search(r'name\s*=\s*"([^"]+)"', block)
            x_match = re.search(r'x\s*=\s*([-\d.]+)', block)
            y_match = re.search(r'y\s*=\s*([-\d.]+)', block)
            amount_match = re.search(r'amount\s*=\s*(\d+)', block)

            if name_match and x_match and y_match and amount_match:
                resources.append(ResourcePatch(
                    name=name_match.group(1),
                    position_x=float(x_match.group(1)),
                    position_y=float(y_match.group(1)),
                    amount=int(amount_match.group(1))
                ))

        return resources

    # -------------------------------------------------------------------------
    # Phase 2: Inventory & Crafting
    # -------------------------------------------------------------------------

    def get_player_inventory(self) -> list[InventoryItem]:
        """
        Get the player's main inventory contents.

        Returns:
            List of InventoryItem objects with name and count.
        """
        lua = '''
(function()
    local inv = game.connected_players[1].get_main_inventory()
    local result = {}
    for i = 1, #inv do
        local stack = inv[i]
        if stack.valid_for_read then
            result[stack.name] = (result[stack.name] or 0) + stack.count
        end
    end
    local items = {}
    for name, count in pairs(result) do
        table.insert(items, {name=name, count=count})
    end
    return items
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return []

        return self._parse_inventory(result)

    def _parse_inventory(self, serpent_output: str) -> list[InventoryItem]:
        """Parse serpent output of inventory."""
        import re
        items = []

        # Pattern: {count = 1, name = "wooden-chest"} (note: spaces, count before name)
        pattern = r'\{count\s*=\s*(\d+),\s*name\s*=\s*"([^"]+)"\}'
        matches = re.findall(pattern, serpent_output)

        for count, name in matches:
            items.append(InventoryItem(name=name, count=int(count)))

        return items

    def get_entity_inventory(self, x: float, y: float) -> list[InventoryItem]:
        """
        Get inventory contents of entity at position.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            List of InventoryItem objects.
        """
        lua = f'''
(function()
    local entities = game.surfaces[1].find_entities_filtered{{position={{{x},{y}}}, radius=1}}
    for _, e in pairs(entities) do
        local inv = e.get_output_inventory() or e.get_inventory(defines.inventory.chest)
        if inv then
            local result = {{}}
            for i = 1, #inv do
                local stack = inv[i]
                if stack.valid_for_read then
                    result[stack.name] = (result[stack.name] or 0) + stack.count
                end
            end
            local items = {{}}
            for name, count in pairs(result) do
                table.insert(items, {{name=name, count=count}})
            end
            return items
        end
    end
    return {{}}
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return []

        return self._parse_inventory(result)

    def craft_item(self, item_name: str, count: int = 1) -> bool:
        """
        Craft items manually (player hand-crafting).

        Args:
            item_name: Name of item to craft (e.g., "iron-gear-wheel")
            count: Number to craft (default 1)

        Returns:
            True if crafting started, False otherwise.
        """
        # Use DOT syntax for begin_crafting
        lua = f'game.connected_players[1].begin_crafting{{recipe="{item_name}", count={count}}}'
        result = self._rcon.query_lua(lua)

        # begin_crafting returns number of items that will be crafted
        try:
            crafted = int(result) if result else 0
            return crafted > 0
        except ValueError:
            return False

    def mine_resource(self, count: int = 10, resource_type: str = None) -> dict:
        """
        Hand-mine resources near the player's position.

        Mines resources within the nearby field (30 tile radius). Can mine
        the entire field in one call - no walking needed. Pass count=-1
        to mine ALL resources of that type in the field.

        Args:
            count: Number of ore to mine (default 10). Use -1 to mine entire field.
            resource_type: Specific resource to mine (e.g., "coal", "iron-ore").
                          If None, mines the first resource type found.

        Returns:
            Dict with resource name, amount mined, and amount remaining in field.
        """
        # Note: entity.mine() doesn't work on resource entities (ore patches).
        # We use direct Lua manipulation which works at any distance within radius.
        # This means we can mine the entire field without the player walking around.

        # -1 means mine everything
        target_lua = "999999999" if count == -1 else str(count)

        # Resource type filter
        type_filter = f'"{resource_type}"' if resource_type else "nil"

        lua = f'''
(function()
    local p = game.connected_players[1]
    local pos = p.position
    local resources = p.surface.find_entities_filtered{{position=pos, type="resource", radius=30}}
    if #resources == 0 then
        return {{error="no_resource"}}
    end
    local target = {target_lua}
    local total_mined = 0
    local wanted = {type_filter}
    local name = wanted or resources[1].name
    local inv = p.get_main_inventory()
    for _, r in ipairs(resources) do
        if r.valid and r.name == name and r.amount > 0 and total_mined < target then
            local to_mine = math.min(target - total_mined, r.amount)
            if to_mine > 0 then
                if to_mine >= r.amount then
                    inv.insert({{name=name, count=r.amount}})
                    total_mined = total_mined + r.amount
                    r.destroy()
                else
                    r.amount = r.amount - to_mine
                    inv.insert({{name=name, count=to_mine}})
                    total_mined = total_mined + to_mine
                end
            end
        end
    end
    local remaining = 0
    for _, r in ipairs(resources) do
        if r.valid and r.name == name then
            remaining = remaining + r.amount
        end
    end
    return {{name=name, mined=total_mined, remaining_in_field=remaining}}
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return {"error": "Failed to execute mining command"}

        # Parse result
        import re
        if "no_resource" in result:
            return {"error": "No resources found within 30 tiles of player"}

        name_match = re.search(r'name\s*=\s*"([^"]+)"', result)
        mined_match = re.search(r'mined\s*=\s*(\d+)', result)
        remaining_match = re.search(r'remaining_in_field\s*=\s*(\d+)', result)

        if name_match:
            mined = int(mined_match.group(1)) if mined_match else 0
            remaining = int(remaining_match.group(1)) if remaining_match else 0
            return {
                "status": "success",
                "resource": name_match.group(1),
                "mined": mined,
                "remaining_in_field": remaining,
                "field_depleted": remaining == 0
            }

        return {"error": "Failed to parse mining result"}

    # -------------------------------------------------------------------------
    # Phase 2: Entity Actions
    # -------------------------------------------------------------------------

    def place_entity(self, name: str, x: float, y: float) -> bool:
        """
        Place an entity at the specified position.

        Args:
            name: Entity name (e.g., "iron-chest", "transport-belt")
            x: X coordinate
            y: Y coordinate

        Returns:
            True if placed successfully, False otherwise.
        """
        # First check if we can place there
        check_lua = f'game.surfaces[1].can_place_entity{{name="{name}", position={{{x},{y}}}, force="player"}}'
        can_place = self._rcon.query_lua(check_lua)

        if can_place != "true":
            return False

        # Place the entity
        place_lua = f'game.surfaces[1].create_entity{{name="{name}", position={{{x},{y}}}, force="player"}}'
        result = self._rcon.query_lua(place_lua)

        # create_entity returns the entity or nil
        return result is not None and "nil" not in result.lower()

    def remove_entity(self, x: float, y: float) -> bool:
        """
        Remove entity at the specified position.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if entity was removed, False otherwise.
        """
        lua = f'''
(function()
    local entities = game.surfaces[1].find_entities_filtered{{position={{{x},{y}}}, radius=0.5}}
    for _, e in pairs(entities) do
        if e.valid and e.name ~= "character" then
            e.destroy()
            return true
        end
    end
    return false
end)()
'''
        result = self._rcon.query_lua(lua.strip().replace('\n', ' '))
        return result == "true"

    # -------------------------------------------------------------------------
    # Phase 2: Factory Analysis
    # -------------------------------------------------------------------------

    def get_assemblers(self, limit: int = 20) -> list[dict]:
        """
        Get list of assembling machines with their recipes.

        Args:
            limit: Maximum number to return (default 20)

        Returns:
            List of dicts with name, position, and recipe.
        """
        lua = f'''
(function()
    local machines = game.surfaces[1].find_entities_filtered{{type="assembling-machine"}}
    local result = {{}}
    local count = 0
    for _, m in pairs(machines) do
        if count >= {limit} then break end
        local recipe = m.get_recipe()
        table.insert(result, {{
            name=m.name,
            x=m.position.x,
            y=m.position.y,
            recipe=recipe and recipe.name or "none"
        }})
        count = count + 1
    end
    return result
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return []

        # Parse assembler list - handle spaces and different field orders
        import re
        assemblers = []
        blocks = re.findall(r'\{[^}]+\}', result)

        for block in blocks:
            name_match = re.search(r'name\s*=\s*"([^"]+)"', block)
            x_match = re.search(r'x\s*=\s*([-\d.]+)', block)
            y_match = re.search(r'y\s*=\s*([-\d.]+)', block)
            recipe_match = re.search(r'recipe\s*=\s*"([^"]*)"', block)

            if name_match and x_match and y_match:
                recipe = recipe_match.group(1) if recipe_match else None
                assemblers.append({
                    "name": name_match.group(1),
                    "x": float(x_match.group(1)),
                    "y": float(y_match.group(1)),
                    "recipe": recipe if recipe != "none" else None
                })

        return assemblers

    def get_power_stats(self) -> dict:
        """
        Get electricity production and consumption stats.

        Returns:
            Dict with production_mw, consumption_mw, satisfaction (0-1).
        """
        lua = '''
(function()
    local network = game.connected_players[1].surface.find_entities_filtered{type="electric-pole"}[1]
    if network and network.electric_network_statistics then
        local stats = network.electric_network_statistics
        return {
            production=stats.get_flow_count{input=true, precision_index=defines.flow_precision_index.one_second},
            consumption=stats.get_flow_count{input=false, precision_index=defines.flow_precision_index.one_second},
            satisfaction=network.electric_network_statistics.satisfaction or 1
        }
    end
    return {production=0, consumption=0, satisfaction=1}
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return {"production_mw": 0, "consumption_mw": 0, "satisfaction": 1.0}

        # Parse power stats - handle spaces around =
        import re
        prod_match = re.search(r'production\s*=\s*(\d+)', result)
        cons_match = re.search(r'consumption\s*=\s*(\d+)', result)
        sat_match = re.search(r'satisfaction\s*=\s*([\d.]+)', result)

        # Convert from watts to MW
        production = int(prod_match.group(1)) / 1_000_000 if prod_match else 0
        consumption = int(cons_match.group(1)) / 1_000_000 if cons_match else 0
        satisfaction = float(sat_match.group(1)) if sat_match else 1.0

        return {
            "production_mw": production,
            "consumption_mw": consumption,
            "satisfaction": satisfaction
        }

    def get_research_status(self) -> dict:
        """
        Get current research progress.

        Returns:
            Dict with current_research, progress (0-1), and research_queue.
        """
        lua = '''
(function()
    local force = game.forces["player"]
    local current = force.current_research
    local progress = force.research_progress
    local queue = {}
    if force.research_queue then
        for i, tech in pairs(force.research_queue) do
            if i <= 5 then table.insert(queue, tech.name) end
        end
    end
    return {
        current=current and current.name or "none",
        progress=progress or 0,
        queue=queue
    }
end)()
'''
        result = self._rcon.query_lua_table(lua.strip().replace('\n', ' '))

        if not result:
            return {"current_research": None, "progress": 0, "research_queue": []}

        # Parse research status - handle spaces around =
        import re
        current_match = re.search(r'current\s*=\s*"([^"]*)"', result)
        progress_match = re.search(r'progress\s*=\s*([\d.]+)', result)

        current = current_match.group(1) if current_match else None
        if current == "none":
            current = None
        progress = float(progress_match.group(1)) if progress_match else 0

        # Parse queue
        queue = []
        queue_match = re.search(r'queue\s*=\s*\{([^}]*)\}', result)
        if queue_match:
            queue = re.findall(r'"([^"]+)"', queue_match.group(1))

        return {
            "current_research": current,
            "progress": progress,
            "research_queue": queue
        }

    # -------------------------------------------------------------------------
    # Context Manager
    # -------------------------------------------------------------------------

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
