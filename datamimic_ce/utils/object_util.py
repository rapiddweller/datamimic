# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from datamimic_ce.contexts.context import Context
from datamimic_ce.utils.string_util import StringUtil


class ObjectUtil:
    @staticmethod
    def create_instance_from_constructor_str(context: Context, constructor_str: str, class_dict: dict[str, type]):
        """
        Create instance from constructor string
        :param context:
        :param constructor_str:
        :param class_dict:
        :return:
        """
        # Get classname from constructor string
        class_name = StringUtil.get_class_name_from_constructor_string(constructor_str)
        cls = class_dict.get(class_name)
        if cls is None:
            cls = context.root.get_dynamic_class(class_name)
            if cls is None:
                raise ValueError(f"Cannot find converter '{class_name}'")

        # Check if a constructor call was found
        if class_name != constructor_str:
            # Try to init instance
            return context.evaluate_python_expression(constructor_str, class_dict)
        # Handle simple instance init (without constructor in attribute value)
        if "CustomConverter" in cls.__base__.__name__:  # Check if class is CustomConverter
            return cls(context)
        else:
            return cls()

    @staticmethod
    def check_valid_property_field(obj: object, attr_name: str, entity_name: str):
        """
        Check valid getter from object, return value if found
        :param obj:
        :param attr_name:
        :param entity_name:
        :return:
        """
        valid_fields = set([name for name, value in vars(obj.__class__).items() if isinstance(value, property)])
        try:
            return getattr(obj, attr_name)
        except AttributeError as e:
            raise AttributeError(
                f"Entity {entity_name} object has no attribute {attr_name}, expects getters: %s" % valid_fields
            ) from e
