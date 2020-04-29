# Copyright 2019-2020 the openage authors. See copying.md for legal info.

"""
Convert API-like objects to nyan objects. Subroutine of the
main AoC processor.
"""
from ...dataformat.aoc.internal_nyan_names import UNIT_LINE_LOOKUPS, CLASS_ID_LOOKUPS,\
    BUILDING_LINE_LOOKUPS, TECH_GROUP_LOOKUPS
from ...dataformat.converter_object import RawAPIObject
from ...dataformat.aoc.genie_unit import GenieVillagerGroup
from .ability_subprocessor import AoCAbilitySubprocessor
from openage.convert.processor.aoc.auxiliary_subprocessor import AoCAuxiliarySubprocessor
from openage.convert.dataformat.aoc.expected_pointer import ExpectedPointer
from openage.convert.dataformat.aoc.genie_tech import UnitLineUpgrade
from openage.convert.dataformat.aoc.genie_unit import GenieBuildingLineGroup,\
    GenieGarrisonMode, GenieMonkGroup, GenieStackBuildingGroup
from openage.convert.dataformat.aoc.internal_nyan_names import AMBIENT_GROUP_LOOKUPS,\
    TERRAIN_GROUP_LOOKUPS, TERRAIN_TYPE_LOOKUPS, CIV_GROUP_LOOKUPS,\
    VARIANT_GROUP_LOOKUPS
from openage.convert.dataformat.aoc.combined_terrain import CombinedTerrain
from openage.convert.processor.aoc.tech_subprocessor import AoCTechSubprocessor
from openage.convert.processor.aoc.civ_subprocessor import AoCCivSubprocessor
from openage.convert.processor.aoc.modifier_subprocessor import AoCModifierSubprocessor
from openage.convert.processor.aoc.upgrade_ability_subprocessor import AoCUgradeAbilitySubprocessor


class AoCNyanSubprocessor:

    @classmethod
    def convert(cls, gamedata):

        cls._process_game_entities(gamedata)
        cls._create_nyan_objects(gamedata)
        cls._create_nyan_members(gamedata)

    @classmethod
    def _create_nyan_objects(cls, full_data_set):
        """
        Creates nyan objects from the API objects.
        """
        for unit_line in full_data_set.unit_lines.values():
            unit_line.create_nyan_objects()

        for building_line in full_data_set.building_lines.values():
            building_line.create_nyan_objects()

        for ambient_group in full_data_set.ambient_groups.values():
            ambient_group.create_nyan_objects()

        for variant_group in full_data_set.variant_groups.values():
            variant_group.create_nyan_objects()

        for tech_group in full_data_set.tech_groups.values():
            tech_group.create_nyan_objects()

        for terrain_group in full_data_set.terrain_groups.values():
            terrain_group.create_nyan_objects()

        for civ_group in full_data_set.civ_groups.values():
            civ_group.create_nyan_objects()

    @classmethod
    def _create_nyan_members(cls, full_data_set):
        """
        Fill nyan member values of the API objects.
        """
        for unit_line in full_data_set.unit_lines.values():
            unit_line.create_nyan_members()

        for building_line in full_data_set.building_lines.values():
            building_line.create_nyan_members()

        for ambient_group in full_data_set.ambient_groups.values():
            ambient_group.create_nyan_members()

        for variant_group in full_data_set.variant_groups.values():
            variant_group.create_nyan_members()

        for tech_group in full_data_set.tech_groups.values():
            tech_group.create_nyan_members()

        for terrain_group in full_data_set.terrain_groups.values():
            terrain_group.create_nyan_members()

        for civ_group in full_data_set.civ_groups.values():
            civ_group.create_nyan_members()

    @classmethod
    def _process_game_entities(cls, full_data_set):

        for unit_line in full_data_set.unit_lines.values():
            cls._unit_line_to_game_entity(unit_line)

        for building_line in full_data_set.building_lines.values():
            cls._building_line_to_game_entity(building_line)

        for ambient_group in full_data_set.ambient_groups.values():
            cls._ambient_group_to_game_entity(ambient_group)

        for variant_group in full_data_set.variant_groups.values():
            cls._variant_group_to_game_entity(variant_group)

        for tech_group in full_data_set.tech_groups.values():
            if tech_group.is_researchable():
                cls._tech_group_to_tech(tech_group)

        for terrain_group in full_data_set.terrain_groups.values():
            cls._terrain_group_to_terrain(terrain_group)

        AoCCivSubprocessor.create_graphics_sets(full_data_set)

        for civ_group in full_data_set.civ_groups.values():
            cls._civ_group_to_civ(civ_group)

    @staticmethod
    def _unit_line_to_game_entity(unit_line):
        """
        Creates raw API objects for a unit line.

        :param unit_line: Unit line that gets converted to a game entity.
        :type unit_line: ..dataformat.converter_object.ConverterObjectGroup
        """
        current_unit = unit_line.get_head_unit()
        current_unit_id = unit_line.get_head_unit_id()

        dataset = unit_line.data

        # Start with the generic GameEntity
        game_entity_name = UNIT_LINE_LOOKUPS[current_unit_id][0]
        obj_location = "data/game_entity/generic/%s/" % (UNIT_LINE_LOOKUPS[current_unit_id][1])
        raw_api_object = RawAPIObject(game_entity_name, game_entity_name,
                                      dataset.nyan_api_objects)
        raw_api_object.add_raw_parent("engine.aux.game_entity.GameEntity")
        raw_api_object.set_location(obj_location)
        raw_api_object.set_filename(UNIT_LINE_LOOKUPS[current_unit_id][1])
        unit_line.add_raw_api_object(raw_api_object)

        # =======================================================================
        # Game Entity Types
        # =======================================================================
        # we give a unit two types
        #    - aux.game_entity_type.types.Unit (if unit_type >= 70)
        #    - aux.game_entity_type.types.<Class> (depending on the class)
        # =======================================================================
        # Create or use existing auxiliary types
        types_set = []
        unit_type = current_unit.get_member("unit_type").get_value()

        if unit_type >= 70:
            type_obj = dataset.pregen_nyan_objects["aux.game_entity_type.types.Unit"].get_nyan_object()
            types_set.append(type_obj)

        unit_class = current_unit.get_member("unit_class").get_value()
        class_name = CLASS_ID_LOOKUPS[unit_class]
        class_obj_name = "aux.game_entity_type.types.%s" % (class_name)
        type_obj = dataset.pregen_nyan_objects[class_obj_name].get_nyan_object()
        types_set.append(type_obj)

        raw_api_object.add_raw_member("types", types_set, "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Abilities
        # =======================================================================
        abilities_set = []

        abilities_set.append(AoCAbilitySubprocessor.death_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.delete_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.despawn_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.idle_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.hitbox_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.live_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.los_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.move_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.named_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.resistance_ability(unit_line))
        abilities_set.extend(AoCAbilitySubprocessor.selectable_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.stop_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.terrain_requirement_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.turn_ability(unit_line))
        abilities_set.append(AoCAbilitySubprocessor.visibility_ability(unit_line))

        # Creation
        if len(unit_line.creates) > 0:
            abilities_set.append(AoCAbilitySubprocessor.create_ability(unit_line))

        # Config
        ability = AoCAbilitySubprocessor.use_contingent_ability(unit_line)
        if ability:
            abilities_set.append(ability)

        if unit_line.get_head_unit_id() in (125, 692):
            # Healing/Recharging attribute points (monks, berserks)
            abilities_set.extend(AoCAbilitySubprocessor.regenerate_attribute_ability(unit_line))

        # Applying effects and shooting projectiles
        if unit_line.is_projectile_shooter():
            abilities_set.append(AoCAbilitySubprocessor.shoot_projectile_ability(unit_line, 7))
            AoCNyanSubprocessor._projectiles_from_line(unit_line)

        elif unit_line.is_melee() or unit_line.is_ranged():
            if unit_line.has_command(7):
                # Attack
                abilities_set.append(AoCAbilitySubprocessor.apply_discrete_effect_ability(unit_line,
                                                                                          7,
                                                                                          unit_line.is_ranged()))

            if unit_line.has_command(101):
                # Build
                abilities_set.append(AoCAbilitySubprocessor.apply_continuous_effect_ability(unit_line,
                                                                                            101,
                                                                                            unit_line.is_ranged()))

            if unit_line.has_command(104):
                # convert
                abilities_set.append(AoCAbilitySubprocessor.apply_discrete_effect_ability(unit_line,
                                                                                          104,
                                                                                          unit_line.is_ranged()))

            if unit_line.has_command(105):
                # Heal
                abilities_set.append(AoCAbilitySubprocessor.apply_continuous_effect_ability(unit_line,
                                                                                            105,
                                                                                            unit_line.is_ranged()))

            if unit_line.has_command(106):
                # Repair
                abilities_set.append(AoCAbilitySubprocessor.apply_continuous_effect_ability(unit_line,
                                                                                            106,
                                                                                            unit_line.is_ranged()))

        # Formation/Stance
        if not isinstance(unit_line, GenieVillagerGroup):
            abilities_set.append(AoCAbilitySubprocessor.formation_ability(unit_line))
            abilities_set.append(AoCAbilitySubprocessor.game_entity_stance_ability(unit_line))

        # Storage abilities
        if unit_line.is_garrison():
            abilities_set.append(AoCAbilitySubprocessor.storage_ability(unit_line))
            abilities_set.append(AoCAbilitySubprocessor.remove_storage_ability(unit_line))

            garrison_mode = unit_line.get_garrison_mode()

            if garrison_mode == GenieGarrisonMode.MONK:
                abilities_set.append(AoCAbilitySubprocessor.collect_storage_ability(unit_line))

        if len(unit_line.garrison_locations) > 0:
            ability = AoCAbilitySubprocessor.enter_container_ability(unit_line)
            if ability:
                abilities_set.append(ability)

            ability = AoCAbilitySubprocessor.exit_container_ability(unit_line)
            if ability:
                abilities_set.append(ability)

        if isinstance(unit_line, GenieMonkGroup):
            abilities_set.append(AoCAbilitySubprocessor.transfer_storage_ability(unit_line))

        # Resource abilities
        if unit_line.is_gatherer():
            abilities_set.append(AoCAbilitySubprocessor.drop_resources_ability(unit_line))
            abilities_set.extend(AoCAbilitySubprocessor.gather_ability(unit_line))
            abilities_set.append(AoCAbilitySubprocessor.resource_storage_ability(unit_line))

        if isinstance(unit_line, GenieVillagerGroup):
            # Farm restocking
            abilities_set.append(AoCAbilitySubprocessor.restock_ability(unit_line, 50))

        if unit_line.is_harvestable():
            abilities_set.append(AoCAbilitySubprocessor.harvestable_ability(unit_line))

        if unit_type == 70 and unit_line.get_class_id() not in (9, 10, 58):
            # Excludes trebuchets and animals
            abilities_set.append(AoCAbilitySubprocessor.herd_ability(unit_line))

        if unit_line.get_class_id() == 58:
            abilities_set.append(AoCAbilitySubprocessor.herdable_ability(unit_line))

        # Trade abilities
        if unit_line.has_command(111):
            abilities_set.append(AoCAbilitySubprocessor.trade_ability(unit_line))

        # =======================================================================
        # TODO: Transform
        # =======================================================================
        raw_api_object.add_raw_member("abilities", abilities_set,
                                      "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Modifiers
        # =======================================================================
        modifiers_set = []

        if unit_line.has_command(7) and not unit_line.is_projectile_shooter():
            modifiers_set.extend(AoCModifierSubprocessor.elevation_attack_modifiers(unit_line))

        if unit_line.is_gatherer():
            modifiers_set.extend(AoCModifierSubprocessor.gather_rate_modifier(unit_line))

        raw_api_object.add_raw_member("modifiers", modifiers_set,
                                      "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # TODO: Variants
        # =======================================================================
        variants_set = []

        raw_api_object.add_raw_member("variants", variants_set,
                                      "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Misc (Objects that are not used by the unit line itself, but use its values)
        # =======================================================================
        if unit_line.is_creatable():
            AoCAuxiliarySubprocessor.get_creatable_game_entity(unit_line)

    @staticmethod
    def _building_line_to_game_entity(building_line):
        """
        Creates raw API objects for a building line.

        :param building_line: Building line that gets converted to a game entity.
        :type building_line: ..dataformat.converter_object.ConverterObjectGroup
        """
        current_building = building_line.line[0]
        current_building_id = building_line.get_head_unit_id()
        dataset = building_line.data

        # Start with the generic GameEntity
        game_entity_name = BUILDING_LINE_LOOKUPS[current_building_id][0]
        obj_location = "data/game_entity/generic/%s/" % (BUILDING_LINE_LOOKUPS[current_building_id][1])
        raw_api_object = RawAPIObject(game_entity_name, game_entity_name,
                                      dataset.nyan_api_objects)
        raw_api_object.add_raw_parent("engine.aux.game_entity.GameEntity")
        raw_api_object.set_location(obj_location)
        raw_api_object.set_filename(BUILDING_LINE_LOOKUPS[current_building_id][1])
        building_line.add_raw_api_object(raw_api_object)

        # =======================================================================
        # Game Entity Types
        # =======================================================================
        # we give a building two types
        #    - aux.game_entity_type.types.Building (if unit_type >= 80)
        #    - aux.game_entity_type.types.<Class> (depending on the class)
        # and additionally
        #    - aux.game_entity_type.types.DropSite (only if this is used as a drop site)
        # =======================================================================
        # Create or use existing auxiliary types
        types_set = []
        unit_type = current_building.get_member("unit_type").get_value()

        if unit_type >= 80:
            type_obj = dataset.pregen_nyan_objects["aux.game_entity_type.types.Building"].get_nyan_object()
            types_set.append(type_obj)

        unit_class = current_building.get_member("unit_class").get_value()
        class_name = CLASS_ID_LOOKUPS[unit_class]
        class_obj_name = "aux.game_entity_type.types.%s" % (class_name)
        type_obj = dataset.pregen_nyan_objects[class_obj_name].get_nyan_object()
        types_set.append(type_obj)

        if building_line.is_dropsite():
            type_obj = dataset.pregen_nyan_objects["aux.game_entity_type.types.DropSite"].get_nyan_object()
            types_set.append(type_obj)

        raw_api_object.add_raw_member("types", types_set, "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Abilities
        # =======================================================================
        abilities_set = []

        abilities_set.append(AoCAbilitySubprocessor.attribute_change_tracker_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.death_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.delete_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.idle_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.hitbox_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.live_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.los_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.named_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.resistance_ability(building_line))
        abilities_set.extend(AoCAbilitySubprocessor.selectable_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.stop_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.terrain_requirement_ability(building_line))
        abilities_set.append(AoCAbilitySubprocessor.visibility_ability(building_line))

        # Config abilities
        if building_line.is_creatable():
            abilities_set.append(AoCAbilitySubprocessor.constructable_ability(building_line))

        if building_line.is_passable() or\
                (isinstance(building_line, GenieStackBuildingGroup) and building_line.is_gate()):
            abilities_set.append(AoCAbilitySubprocessor.passable_ability(building_line))

        if building_line.has_foundation():
            if building_line.get_class_id() == 49:
                # Use OverlayTerrain for the farm terrain
                abilities_set.append(AoCAbilitySubprocessor.overlay_terrain_ability(building_line))
                abilities_set.append(AoCAbilitySubprocessor.foundation_ability(building_line,
                                                                               terrain_id=27))

            else:
                abilities_set.append(AoCAbilitySubprocessor.foundation_ability(building_line))

        # Creation/Research abilities
        if len(building_line.creates) > 0:
            abilities_set.append(AoCAbilitySubprocessor.create_ability(building_line))
            abilities_set.append(AoCAbilitySubprocessor.production_queue_ability(building_line))

        if len(building_line.researches) > 0:
            abilities_set.append(AoCAbilitySubprocessor.research_ability(building_line))

        # Effect abilities
        if building_line.is_projectile_shooter():
            abilities_set.append(AoCAbilitySubprocessor.shoot_projectile_ability(building_line, 7))
            abilities_set.append(AoCAbilitySubprocessor.game_entity_stance_ability(building_line))
            AoCNyanSubprocessor._projectiles_from_line(building_line)

        # Storage abilities
        if building_line.is_garrison():
            abilities_set.append(AoCAbilitySubprocessor.storage_ability(building_line))
            abilities_set.append(AoCAbilitySubprocessor.remove_storage_ability(building_line))

            garrison_mode = building_line.get_garrison_mode()

            if garrison_mode == GenieGarrisonMode.NATURAL:
                abilities_set.append(AoCAbilitySubprocessor.send_back_to_task_ability(building_line))

            if garrison_mode in (GenieGarrisonMode.NATURAL, GenieGarrisonMode.SELF_PRODUCED):
                abilities_set.append(AoCAbilitySubprocessor.rally_point_ability(building_line))

        # Resource abilities
        if building_line.is_harvestable():
            abilities_set.append(AoCAbilitySubprocessor.harvestable_ability(building_line))

        if building_line.is_dropsite():
            abilities_set.append(AoCAbilitySubprocessor.drop_site_ability(building_line))

        ability = AoCAbilitySubprocessor.provide_contingent_ability(building_line)
        if ability:
            abilities_set.append(ability)

        # Trade abilities
        if building_line.is_trade_post():
            abilities_set.append(AoCAbilitySubprocessor.trade_post_ability(building_line))

        if building_line.get_id() == 84:
            # Market trading
            abilities_set.extend(AoCAbilitySubprocessor.exchange_resources_ability(building_line))

        raw_api_object.add_raw_member("abilities", abilities_set,
                                      "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Modifiers
        # =======================================================================
        raw_api_object.add_raw_member("modifiers", [], "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # TODO: Variants
        # =======================================================================
        raw_api_object.add_raw_member("variants", [], "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Misc (Objects that are not used by the unit line itself, but use its values)
        # =======================================================================
        if building_line.is_creatable():
            AoCAuxiliarySubprocessor.get_creatable_game_entity(building_line)

    @staticmethod
    def _ambient_group_to_game_entity(ambient_group):
        """
        Creates raw API objects for an ambient group.

        :param ambient_group: Unit line that gets converted to a game entity.
        :type ambient_group: ..dataformat.converter_object.ConverterObjectGroup
        """
        ambient_unit = ambient_group.get_head_unit()
        ambient_id = ambient_group.get_head_unit_id()

        dataset = ambient_group.data

        # Start with the generic GameEntity
        game_entity_name = AMBIENT_GROUP_LOOKUPS[ambient_id][0]
        obj_location = "data/game_entity/generic/%s/" % (AMBIENT_GROUP_LOOKUPS[ambient_id][1])
        raw_api_object = RawAPIObject(game_entity_name, game_entity_name,
                                      dataset.nyan_api_objects)
        raw_api_object.add_raw_parent("engine.aux.game_entity.GameEntity")
        raw_api_object.set_location(obj_location)
        raw_api_object.set_filename(AMBIENT_GROUP_LOOKUPS[ambient_id][1])
        ambient_group.add_raw_api_object(raw_api_object)

        # =======================================================================
        # Game Entity Types
        # =======================================================================
        # we give an ambient the types
        #    - aux.game_entity_type.types.Ambient
        # =======================================================================
        # Create or use existing auxiliary types
        types_set = []

        type_obj = dataset.pregen_nyan_objects["aux.game_entity_type.types.Ambient"].get_nyan_object()
        types_set.append(type_obj)

        unit_class = ambient_unit.get_member("unit_class").get_value()
        class_name = CLASS_ID_LOOKUPS[unit_class]
        class_obj_name = "aux.game_entity_type.types.%s" % (class_name)
        type_obj = dataset.pregen_nyan_objects[class_obj_name].get_nyan_object()
        types_set.append(type_obj)

        raw_api_object.add_raw_member("types", types_set, "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Abilities
        # =======================================================================
        abilities_set = []

        interaction_mode = ambient_unit.get_member("interaction_mode").get_value()

        if interaction_mode >= 0:
            abilities_set.append(AoCAbilitySubprocessor.death_ability(ambient_group))
            abilities_set.append(AoCAbilitySubprocessor.hitbox_ability(ambient_group))
            abilities_set.append(AoCAbilitySubprocessor.idle_ability(ambient_group))
            abilities_set.append(AoCAbilitySubprocessor.live_ability(ambient_group))
            abilities_set.append(AoCAbilitySubprocessor.named_ability(ambient_group))
            abilities_set.append(AoCAbilitySubprocessor.resistance_ability(ambient_group))
            abilities_set.append(AoCAbilitySubprocessor.terrain_requirement_ability(ambient_group))
            abilities_set.append(AoCAbilitySubprocessor.visibility_ability(ambient_group))

        if interaction_mode >= 2:
            abilities_set.extend(AoCAbilitySubprocessor.selectable_ability(ambient_group))

            if ambient_group.is_passable():
                abilities_set.append(AoCAbilitySubprocessor.passable_ability(ambient_group))

        if ambient_group.is_harvestable():
            abilities_set.append(AoCAbilitySubprocessor.harvestable_ability(ambient_group))

        # =======================================================================
        # Abilities
        # =======================================================================
        raw_api_object.add_raw_member("abilities", abilities_set,
                                      "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Modifiers
        # =======================================================================
        modifiers_set = []

        raw_api_object.add_raw_member("modifiers", modifiers_set,
                                      "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # TODO: Variants
        # =======================================================================
        variants_set = []

        raw_api_object.add_raw_member("variants", variants_set,
                                      "engine.aux.game_entity.GameEntity")

    @staticmethod
    def _variant_group_to_game_entity(variant_group):
        """
        Creates raw API objects for a variant group.

        :param ambient_group: Unit line that gets converted to a game entity.
        :type ambient_group: ..dataformat.converter_object.ConverterObjectGroup
        """
        variant_main_unit = variant_group.get_head_unit()
        variant_id = variant_group.get_head_unit_id()

        dataset = variant_group.data

        # Start with the generic GameEntity
        game_entity_name = VARIANT_GROUP_LOOKUPS[variant_id][0]
        obj_location = "data/game_entity/generic/%s/" % (VARIANT_GROUP_LOOKUPS[variant_id][1])
        raw_api_object = RawAPIObject(game_entity_name, game_entity_name,
                                      dataset.nyan_api_objects)
        raw_api_object.add_raw_parent("engine.aux.game_entity.GameEntity")
        raw_api_object.set_location(obj_location)
        raw_api_object.set_filename(VARIANT_GROUP_LOOKUPS[variant_id][1])
        variant_group.add_raw_api_object(raw_api_object)

        # =======================================================================
        # Game Entity Types
        # =======================================================================
        # we give variants the types
        #    - aux.game_entity_type.types.Ambient
        # =======================================================================
        # Create or use existing auxiliary types
        types_set = []

        type_obj = dataset.pregen_nyan_objects["aux.game_entity_type.types.Ambient"].get_nyan_object()
        types_set.append(type_obj)

        unit_class = variant_main_unit.get_member("unit_class").get_value()
        class_name = CLASS_ID_LOOKUPS[unit_class]
        class_obj_name = "aux.game_entity_type.types.%s" % (class_name)
        type_obj = dataset.pregen_nyan_objects[class_obj_name].get_nyan_object()
        types_set.append(type_obj)

        raw_api_object.add_raw_member("types", types_set, "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Abilities
        # =======================================================================
        abilities_set = []

        abilities_set.append(AoCAbilitySubprocessor.death_ability(variant_group))
        abilities_set.append(AoCAbilitySubprocessor.despawn_ability(variant_group))
        abilities_set.append(AoCAbilitySubprocessor.idle_ability(variant_group))
        abilities_set.append(AoCAbilitySubprocessor.named_ability(variant_group))
        abilities_set.extend(AoCAbilitySubprocessor.selectable_ability(variant_group))
        abilities_set.append(AoCAbilitySubprocessor.terrain_requirement_ability(variant_group))
        abilities_set.append(AoCAbilitySubprocessor.visibility_ability(variant_group))

        if variant_main_unit.has_member("speed") and variant_main_unit["speed"].get_value() > 0:
            abilities_set.append(AoCAbilitySubprocessor.move_ability(variant_group))

        if variant_group.is_harvestable():
            abilities_set.append(AoCAbilitySubprocessor.harvestable_ability(variant_group))

        raw_api_object.add_raw_member("abilities", abilities_set,
                                      "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Modifiers
        # =======================================================================
        modifiers_set = []

        raw_api_object.add_raw_member("modifiers", modifiers_set,
                                      "engine.aux.game_entity.GameEntity")

        # =======================================================================
        # Variants
        # =======================================================================
        variants_set = []

        variant_type = VARIANT_GROUP_LOOKUPS[variant_id][3]

        index = 0
        for variant in variant_group.line:
            # Create a diff
            diff_variant = variant_main_unit.diff(variant)

            if variant_type == "random":
                variant_type_ref = "engine.aux.variant.type.RandomVariant"

            elif variant_type == "angle":
                variant_type_ref = "engine.aux.variant.type.PerspectiveVariant"

            elif variant_type == "misc":
                variant_type_ref = "engine.aux.variant.type.MiscVariant"

            variant_name = "Variant%s" % (str(index))
            variant_ref = "%s.%s" % (game_entity_name, variant_name)
            variant_raw_api_object = RawAPIObject(variant_ref,
                                                  variant_name,
                                                  dataset.nyan_api_objects)
            variant_raw_api_object.add_raw_parent(variant_type_ref)
            variant_location = ExpectedPointer(variant_group, game_entity_name)
            variant_raw_api_object.set_location(variant_location)

            # Create patches for the diff
            patches = []

            patches.extend(AoCUgradeAbilitySubprocessor.death_ability(variant_group,
                                                                      variant_group,
                                                                      variant_ref,
                                                                      diff_variant))
            patches.extend(AoCUgradeAbilitySubprocessor.despawn_ability(variant_group,
                                                                        variant_group,
                                                                        variant_ref,
                                                                        diff_variant))
            patches.extend(AoCUgradeAbilitySubprocessor.idle_ability(variant_group,
                                                                     variant_group,
                                                                     variant_ref,
                                                                     diff_variant))
            patches.extend(AoCUgradeAbilitySubprocessor.named_ability(variant_group,
                                                                      variant_group,
                                                                      variant_ref,
                                                                      diff_variant))

            if variant_main_unit.has_member("speed") and variant_main_unit["speed"].get_value() > 0:
                patches.extend(AoCUgradeAbilitySubprocessor.move_ability(variant_group,
                                                                         variant_group,
                                                                         variant_ref,
                                                                         diff_variant))

            # Changes
            variant_raw_api_object.add_raw_member("changes",
                                                  patches,
                                                  "engine.aux.variant.Variant")

            # Prority
            variant_raw_api_object.add_raw_member("priority",
                                                  1,
                                                  "engine.aux.variant.Variant")

            if variant_type == "random":
                variant_raw_api_object.add_raw_member("chance_share",
                                                      1 / len(variant_group.line),
                                                      "engine.aux.variant.type.RandomVariant")

            elif variant_type == "angle":
                variant_raw_api_object.add_raw_member("angle",
                                                      index,
                                                      "engine.aux.variant.type.PerspectiveVariant")

            variants_expected_pointer = ExpectedPointer(variant_group, variant_ref)
            variants_set.append(variants_expected_pointer)
            variant_group.add_raw_api_object(variant_raw_api_object)

            index += 1

        raw_api_object.add_raw_member("variants", variants_set,
                                      "engine.aux.game_entity.GameEntity")

    @staticmethod
    def _tech_group_to_tech(tech_group):
        """
        Creates raw API objects for a tech group.

        :param tech_group: Tech group that gets converted to a tech.
        :type tech_group: ..dataformat.converter_object.ConverterObjectGroup
        """
        tech_id = tech_group.get_id()

        # Skip Dark Age tech
        if tech_id == 104:
            return

        dataset = tech_group.data

        # Start with the Tech object
        tech_name = TECH_GROUP_LOOKUPS[tech_id][0]
        raw_api_object = RawAPIObject(tech_name, tech_name,
                                      dataset.nyan_api_objects)
        raw_api_object.add_raw_parent("engine.aux.tech.Tech")

        if isinstance(tech_group, UnitLineUpgrade):
            unit_line = dataset.unit_lines_vertical_ref[tech_group.get_line_id()]
            head_unit_id = unit_line.get_head_unit_id()
            obj_location = "data/game_entity/generic/%s/" % (UNIT_LINE_LOOKUPS[head_unit_id][1])

        else:
            obj_location = "data/tech/generic/%s/" % (TECH_GROUP_LOOKUPS[tech_id][1])

        raw_api_object.set_location(obj_location)
        raw_api_object.set_filename(TECH_GROUP_LOOKUPS[tech_id][1])
        tech_group.add_raw_api_object(raw_api_object)

        # =======================================================================
        # Types
        # =======================================================================
        raw_api_object.add_raw_member("types", [], "engine.aux.tech.Tech")

        # =======================================================================
        # Name
        # =======================================================================
        name_ref = "%s.%sName" % (tech_name, tech_name)
        name_raw_api_object = RawAPIObject(name_ref,
                                           "%sName"  % (tech_name),
                                           dataset.nyan_api_objects)
        name_raw_api_object.add_raw_parent("engine.aux.translated.type.TranslatedString")
        name_location = ExpectedPointer(tech_group, tech_name)
        name_raw_api_object.set_location(name_location)

        name_raw_api_object.add_raw_member("translations",
                                           [],
                                           "engine.aux.translated.type.TranslatedString")

        name_expected_pointer = ExpectedPointer(tech_group, name_ref)
        raw_api_object.add_raw_member("name", name_expected_pointer, "engine.aux.tech.Tech")
        tech_group.add_raw_api_object(name_raw_api_object)

        # =======================================================================
        # Description
        # =======================================================================
        description_ref = "%s.%sDescription" % (tech_name, tech_name)
        description_raw_api_object = RawAPIObject(description_ref,
                                                  "%sDescription"  % (tech_name),
                                                  dataset.nyan_api_objects)
        description_raw_api_object.add_raw_parent("engine.aux.translated.type.TranslatedMarkupFile")
        description_location = ExpectedPointer(tech_group, tech_name)
        description_raw_api_object.set_location(description_location)

        description_raw_api_object.add_raw_member("translations",
                                                  [],
                                                  "engine.aux.translated.type.TranslatedMarkupFile")

        description_expected_pointer = ExpectedPointer(tech_group, description_ref)
        raw_api_object.add_raw_member("description",
                                      description_expected_pointer,
                                      "engine.aux.tech.Tech")
        tech_group.add_raw_api_object(description_raw_api_object)

        # =======================================================================
        # Long description
        # =======================================================================
        long_description_ref = "%s.%sLongDescription" % (tech_name, tech_name)
        long_description_raw_api_object = RawAPIObject(long_description_ref,
                                                       "%sLongDescription"  % (tech_name),
                                                       dataset.nyan_api_objects)
        long_description_raw_api_object.add_raw_parent("engine.aux.translated.type.TranslatedMarkupFile")
        long_description_location = ExpectedPointer(tech_group, tech_name)
        long_description_raw_api_object.set_location(long_description_location)

        long_description_raw_api_object.add_raw_member("translations",
                                                       [],
                                                       "engine.aux.translated.type.TranslatedMarkupFile")

        long_description_expected_pointer = ExpectedPointer(tech_group, long_description_ref)
        raw_api_object.add_raw_member("long_description",
                                      long_description_expected_pointer,
                                      "engine.aux.tech.Tech")
        tech_group.add_raw_api_object(long_description_raw_api_object)

        # =======================================================================
        # Updates
        # =======================================================================
        patches = []
        patches.extend(AoCTechSubprocessor.get_patches(tech_group))
        raw_api_object.add_raw_member("updates", patches, "engine.aux.tech.Tech")

        # =======================================================================
        # Misc (Objects that are not used by the tech group itself, but use its values)
        # =======================================================================
        if tech_group.is_researchable():
            AoCAuxiliarySubprocessor.get_researchable_tech(tech_group)

    @staticmethod
    def _terrain_group_to_terrain(terrain_group):
        """
        Creates raw API objects for a terrain group.

        :param terrain_group: Terrain group that gets converted to a tech.
        :type terrain_group: ..dataformat.converter_object.ConverterObjectGroup
        """
        terrain_index = terrain_group.get_id()

        dataset = terrain_group.data

        # Start with the Terrain object
        terrain_name = TERRAIN_GROUP_LOOKUPS[terrain_index][1]
        raw_api_object = RawAPIObject(terrain_name, terrain_name,
                                      dataset.nyan_api_objects)
        raw_api_object.add_raw_parent("engine.aux.terrain.Terrain")
        obj_location = "data/terrain/%s/" % (TERRAIN_GROUP_LOOKUPS[terrain_index][2])
        raw_api_object.set_location(obj_location)
        raw_api_object.set_filename(TERRAIN_GROUP_LOOKUPS[terrain_index][2])
        terrain_group.add_raw_api_object(raw_api_object)

        # =======================================================================
        # Types
        # =======================================================================
        terrain_types = []

        for terrain_type in TERRAIN_TYPE_LOOKUPS.values():
            if terrain_index in terrain_type[0]:
                type_name = "aux.terrain_type.types.%s" % (terrain_type[2])
                type_obj = dataset.pregen_nyan_objects[type_name].get_nyan_object()
                terrain_types.append(type_obj)

        raw_api_object.add_raw_member("types", terrain_types, "engine.aux.terrain.Terrain")

        # =======================================================================
        # Name
        # =======================================================================
        name_ref = "%s.%sName" % (terrain_name, terrain_name)
        name_raw_api_object = RawAPIObject(name_ref,
                                           "%sName"  % (terrain_name),
                                           dataset.nyan_api_objects)
        name_raw_api_object.add_raw_parent("engine.aux.translated.type.TranslatedString")
        name_location = ExpectedPointer(terrain_group, terrain_name)
        name_raw_api_object.set_location(name_location)

        name_raw_api_object.add_raw_member("translations",
                                           [],
                                           "engine.aux.translated.type.TranslatedString")

        name_expected_pointer = ExpectedPointer(terrain_group, name_ref)
        raw_api_object.add_raw_member("name", name_expected_pointer, "engine.aux.terrain.Terrain")
        terrain_group.add_raw_api_object(name_raw_api_object)

        # =======================================================================
        # Sound
        # =======================================================================
        sound_name = "%s.Sound" % (terrain_name)
        sound_raw_api_object = RawAPIObject(sound_name, "Sound",
                                            dataset.nyan_api_objects)
        sound_raw_api_object.add_raw_parent("engine.aux.sound.Sound")
        sound_location = ExpectedPointer(terrain_group, terrain_name)
        sound_raw_api_object.set_location(sound_location)

        # Sounds for terrains don't exist in AoC
        sounds = []

        sound_raw_api_object.add_raw_member("play_delay",
                                            0,
                                            "engine.aux.sound.Sound")
        sound_raw_api_object.add_raw_member("sounds",
                                            sounds,
                                            "engine.aux.sound.Sound")

        sound_expected_pointer = ExpectedPointer(terrain_group, sound_name)
        raw_api_object.add_raw_member("sound",
                                      sound_expected_pointer,
                                      "engine.aux.terrain.Terrain")

        terrain_group.add_raw_api_object(sound_raw_api_object)

        # =======================================================================
        # Ambience
        # =======================================================================
        terrain = terrain_group.get_terrain()
        ambients_count = terrain["terrain_units_used_count"].get_value()

        ambience = []
        for ambient_index in range(ambients_count):
            ambient_id = terrain["terrain_unit_id"][ambient_index].get_value()
            ambient_line = dataset.unit_ref[ambient_id]
            ambient_name = AMBIENT_GROUP_LOOKUPS[ambient_line.get_head_unit_id()][0]

            ambient_ref = "%s.Ambient%s" % (terrain_name, str(ambient_index))
            ambient_raw_api_object = RawAPIObject(ambient_ref,
                                                  "Ambient%s" % (str(ambient_index)),
                                                  dataset.nyan_api_objects)
            ambient_raw_api_object.add_raw_parent("engine.aux.terrain.TerrainAmbient")
            ambient_location = ExpectedPointer(terrain_group, terrain_name)
            ambient_raw_api_object.set_location(ambient_location)

            # Game entity reference
            ambient_line_expected_pointer = ExpectedPointer(ambient_line, ambient_name)
            ambient_raw_api_object.add_raw_member("object",
                                                  ambient_line_expected_pointer,
                                                  "engine.aux.terrain.TerrainAmbient")

            # Max density
            max_density = terrain["terrain_unit_density"][ambient_index].get_value()
            ambient_raw_api_object.add_raw_member("max_density",
                                                  max_density,
                                                  "engine.aux.terrain.TerrainAmbient")

            terrain_group.add_raw_api_object(ambient_raw_api_object)
            terrain_ambient_expected_pointer = ExpectedPointer(terrain_group, ambient_ref)
            ambience.append(terrain_ambient_expected_pointer)

        raw_api_object.add_raw_member("ambience", ambience, "engine.aux.terrain.Terrain")

        # =======================================================================
        # Graphic
        # =======================================================================
        if terrain_group.has_subterrain():
            subterrain = terrain_group.get_subterrain()
            slp_id = subterrain["slp_id"].get_value()

        else:
            slp_id = terrain_group.get_terrain()["slp_id"].get_value()

        # Create animation object
        graphic_name = "%s.TerrainTexture" % (terrain_name)
        graphic_raw_api_object = RawAPIObject(graphic_name, "TerrainTexture",
                                              dataset.nyan_api_objects)
        graphic_raw_api_object.add_raw_parent("engine.aux.graphics.Terrain")
        graphic_location = ExpectedPointer(terrain_group, terrain_name)
        graphic_raw_api_object.set_location(graphic_location)

        if slp_id in dataset.combined_terrains.keys():
            terrain_graphic = dataset.combined_terrains[slp_id]

        else:
            terrain_graphic = CombinedTerrain(slp_id,
                                              "texture_%s" % (TERRAIN_GROUP_LOOKUPS[terrain_index][2]),
                                              dataset)
            dataset.combined_terrains.update({terrain_graphic.get_id(): terrain_graphic})

        terrain_graphic.add_reference(graphic_raw_api_object)

        graphic_raw_api_object.add_raw_member("sprite", terrain_graphic,
                                              "engine.aux.graphics.Terrain")

        terrain_group.add_raw_api_object(graphic_raw_api_object)
        graphic_expected_pointer = ExpectedPointer(terrain_group, graphic_name)
        raw_api_object.add_raw_member("terrain_graphic", graphic_expected_pointer,
                                      "engine.aux.terrain.Terrain")

    @staticmethod
    def _civ_group_to_civ(civ_group):
        """
        Creates raw API objects for a civ group.

        :param civ_group: Terrain group that gets converted to a tech.
        :type civ_group: ..dataformat.converter_object.ConverterObjectGroup
        """
        civ_id = civ_group.get_id()

        dataset = civ_group.data

        # Start with the Tech object
        tech_name = CIV_GROUP_LOOKUPS[civ_id][0]
        raw_api_object = RawAPIObject(tech_name, tech_name,
                                      dataset.nyan_api_objects)
        raw_api_object.add_raw_parent("engine.aux.civilization.Civilization")

        obj_location = "data/civ/%s/" % (CIV_GROUP_LOOKUPS[civ_id][1])

        raw_api_object.set_location(obj_location)
        raw_api_object.set_filename(CIV_GROUP_LOOKUPS[civ_id][1])
        civ_group.add_raw_api_object(raw_api_object)

        # =======================================================================
        # Name
        # =======================================================================
        name_ref = "%s.%sName" % (tech_name, tech_name)
        name_raw_api_object = RawAPIObject(name_ref,
                                           "%sName"  % (tech_name),
                                           dataset.nyan_api_objects)
        name_raw_api_object.add_raw_parent("engine.aux.translated.type.TranslatedString")
        name_location = ExpectedPointer(civ_group, tech_name)
        name_raw_api_object.set_location(name_location)

        name_raw_api_object.add_raw_member("translations",
                                           [],
                                           "engine.aux.translated.type.TranslatedString")

        name_expected_pointer = ExpectedPointer(civ_group, name_ref)
        raw_api_object.add_raw_member("name", name_expected_pointer, "engine.aux.civilization.Civilization")
        civ_group.add_raw_api_object(name_raw_api_object)

        # =======================================================================
        # Description
        # =======================================================================
        description_ref = "%s.%sDescription" % (tech_name, tech_name)
        description_raw_api_object = RawAPIObject(description_ref,
                                                  "%sDescription"  % (tech_name),
                                                  dataset.nyan_api_objects)
        description_raw_api_object.add_raw_parent("engine.aux.translated.type.TranslatedMarkupFile")
        description_location = ExpectedPointer(civ_group, tech_name)
        description_raw_api_object.set_location(description_location)

        description_raw_api_object.add_raw_member("translations",
                                                  [],
                                                  "engine.aux.translated.type.TranslatedMarkupFile")

        description_expected_pointer = ExpectedPointer(civ_group, description_ref)
        raw_api_object.add_raw_member("description",
                                      description_expected_pointer,
                                      "engine.aux.civilization.Civilization")
        civ_group.add_raw_api_object(description_raw_api_object)

        # =======================================================================
        # Long description
        # =======================================================================
        long_description_ref = "%s.%sLongDescription" % (tech_name, tech_name)
        long_description_raw_api_object = RawAPIObject(long_description_ref,
                                                       "%sLongDescription"  % (tech_name),
                                                       dataset.nyan_api_objects)
        long_description_raw_api_object.add_raw_parent("engine.aux.translated.type.TranslatedMarkupFile")
        long_description_location = ExpectedPointer(civ_group, tech_name)
        long_description_raw_api_object.set_location(long_description_location)

        long_description_raw_api_object.add_raw_member("translations",
                                                       [],
                                                       "engine.aux.translated.type.TranslatedMarkupFile")

        long_description_expected_pointer = ExpectedPointer(civ_group, long_description_ref)
        raw_api_object.add_raw_member("long_description",
                                      long_description_expected_pointer,
                                      "engine.aux.civilization.Civilization")
        civ_group.add_raw_api_object(long_description_raw_api_object)

        # =======================================================================
        # TODO: Leader names
        # =======================================================================
        raw_api_object.add_raw_member("leader_names",
                                      [],
                                      "engine.aux.civilization.Civilization")

        # =======================================================================
        # Modifiers
        # =======================================================================
        modifiers = AoCCivSubprocessor.get_civ_setup(civ_group)
        raw_api_object.add_raw_member("modifiers",
                                      modifiers,
                                      "engine.aux.civilization.Civilization")

        # =======================================================================
        # Starting resources
        # =======================================================================
        resource_amounts = AoCCivSubprocessor.get_starting_resources(civ_group)
        raw_api_object.add_raw_member("starting_resources",
                                      resource_amounts,
                                      "engine.aux.civilization.Civilization")

        # =======================================================================
        # Civ setup
        # =======================================================================
        civ_setup = AoCCivSubprocessor.get_civ_setup(civ_group)
        raw_api_object.add_raw_member("civ_setup",
                                      civ_setup,
                                      "engine.aux.civilization.Civilization")

    @staticmethod
    def _projectiles_from_line(line):
        """
        Creates Projectile(GameEntity) raw API objects for a unit/building line.

        :param line: Line for which the projectiles are extracted.
        :type line: ..dataformat.converter_object.ConverterObjectGroup
        """
        current_unit = line.get_head_unit()
        current_unit_id = line.get_head_unit_id()
        dataset = line.data

        if isinstance(line, GenieBuildingLineGroup):
            game_entity_name = BUILDING_LINE_LOOKUPS[current_unit_id][0]
            game_entity_filename = BUILDING_LINE_LOOKUPS[current_unit_id][1]

        else:
            game_entity_name = UNIT_LINE_LOOKUPS[current_unit_id][0]
            game_entity_filename = UNIT_LINE_LOOKUPS[current_unit_id][1]

        projectiles_location = "data/game_entity/generic/%s/projectiles/" % (game_entity_filename)

        projectile_indices = []
        projectile_primary = current_unit.get_member("attack_projectile_primary_unit_id").get_value()
        if projectile_primary > -1:
            projectile_indices.append(0)

        projectile_secondary = current_unit.get_member("attack_projectile_secondary_unit_id").get_value()
        if projectile_secondary > -1:
            projectile_indices.append(1)

        for projectile_num in projectile_indices:
            obj_ref = "%s.ShootProjectile.Projectile%s" % (game_entity_name,
                                                           str(projectile_num))
            obj_name = "Projectile%s" % (str(projectile_num))
            proj_raw_api_object = RawAPIObject(obj_ref, obj_name, dataset.nyan_api_objects)
            proj_raw_api_object.add_raw_parent("engine.aux.game_entity.GameEntity")
            proj_raw_api_object.set_location(projectiles_location)
            proj_raw_api_object.set_filename("%s_projectiles" % (game_entity_filename))

            # =======================================================================
            # Types
            # =======================================================================
            types_set = [dataset.pregen_nyan_objects["aux.game_entity_type.types.Projectile"].get_nyan_object()]
            proj_raw_api_object.add_raw_member("types", types_set, "engine.aux.game_entity.GameEntity")

            # =======================================================================
            # Abilities
            # =======================================================================
            abilities_set = []
            abilities_set.append(AoCAbilitySubprocessor.projectile_ability(line, position=projectile_num))
            abilities_set.append(AoCAbilitySubprocessor.move_projectile_ability(line, position=projectile_num))
            abilities_set.append(AoCAbilitySubprocessor.apply_discrete_effect_ability(line, 7, False, projectile_num))
            # TODO: Death, Despawn
            proj_raw_api_object.add_raw_member("abilities", abilities_set, "engine.aux.game_entity.GameEntity")

            # =======================================================================
            # Modifiers
            # =======================================================================
            modifiers_set = []

            modifiers_set.append(AoCModifierSubprocessor.flyover_effect_modifier(line))
            modifiers_set.extend(AoCModifierSubprocessor.elevation_attack_modifiers(line))

            proj_raw_api_object.add_raw_member("modifiers", modifiers_set, "engine.aux.game_entity.GameEntity")

            # =======================================================================
            # Variants
            # =======================================================================
            variants_set = []
            proj_raw_api_object.add_raw_member("variants", variants_set, "engine.aux.game_entity.GameEntity")

            line.add_raw_api_object(proj_raw_api_object)
