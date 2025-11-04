import customtkinter as ctk
import tkinter as tk
import os
import json
from customtkinter import ThemeManager as CTkThemeManager

class DynamicThemeManager:
    """
    Manages loading and applying themes to customtkinter widgets in an application.
    
    This class handles scanning for theme JSON files, loading the selected theme, 
    and recursively applying the theme properties to existing CTk widgets in the GUI.
    """
    def __init__(self, root_window, theme_dir="themes"):
        """
        Initializes the Theme Manager.
        
        Args:
            root_window (ctk.CTk or tk.Tk): The root window of the application.
            theme_dir (str): The path to the directory containing theme JSON files.
        """
        self.root_window = root_window
        self.theme_dir = theme_dir
        
    def get_available_themes(self):
        """
        Scans the theme directory for .json files and returns a list of theme names 
        (filename without extension).
        
        Returns:
            list: A sorted list of available theme names.
        """
        theme_list = []
        if os.path.exists(self.theme_dir):
            # Iterate through files in the specified directory
            for filename in os.listdir(self.theme_dir):
                # Check if the file is a JSON theme file
                if filename.endswith(".json"):
                    # Remove the .json extension to get the theme name
                    theme_name = os.path.splitext(filename)[0]
                    theme_list.append(theme_name)
        return sorted(theme_list)

    def load_and_apply_theme(self, theme_name):
        """
        Loads a theme file and applies it to the application's widgets.
        
        Args:
            theme_name (str): The name of the theme (e.g., "GreyGhost").
        """
        # Do not apply theme if the default "Choose Style" option is selected
        if theme_name in ("Choose Style", None):
            return

        theme_path = os.path.join(self.theme_dir, f"{theme_name}.json")
        
        if not os.path.exists(theme_path):
            print(f"Theme file not found: {theme_path}")
            return
        
        try:
            # Load the theme using customtkinter's internal mechanism.
            # Note: In CTk 5.0+, the ThemeManager.load_theme() modifies the internal 
            # state of CTk, but often doesn't automatically reconfigure existing widgets 
            # unless they are explicitly told to. We handle this re-configuration 
            # in the _apply_theme_recursively method.
            CTkThemeManager.load_theme(theme_path)
            
            # Recursively apply the loaded theme to existing widgets in the GUI
            self._apply_theme_recursively(self.root_window)
            
            print(f"Theme '{theme_name}' applied successfully.")
            
        except Exception as e:
            print(f"Error loading or applying theme: {e}")

    def _apply_theme_recursively(self, parent_widget):
        """
        Recursively traverses the widget tree and attempts to reconfigure 
        customtkinter widgets with the currently loaded theme.
        
        Args:
            parent_widget (tk.Widget): The widget to start traversal from.
        """
        
        # Iterate through children. We use 'winfo_children()' for standard Tkinter widget traversal.
        # However, CTk widgets often manage their own children differently or through
        # Tkinter's internal mechanism.
        # The most reliable way to force CTk widgets to update their appearance 
        # according to the current theme is to configure their appearance properties 
        # based on the ThemeManager.theme dictionary.

        # Attempt to configure the current widget
        self._reconfigure_widget(parent_widget)

        # Recurse through all children widgets
        for widget in parent_widget.winfo_children():
            self._apply_theme_recursively(widget)

    def _reconfigure_widget(self, widget):
        """
        Manually reconfigures the properties of a specific customtkinter widget 
        based on the currently loaded theme data in ThemeManager.
        
        Args:
            widget (tk.Widget): The widget to configure.
        """
        # Ensure the widget has a configure method and access the theme data
        if not hasattr(widget, 'configure'):
            return

        theme = CTkThemeManager.theme
        widget_type = widget.__class__.__name__

        # --- Widget-specific configuration based on theme data ---
        
        try:
            if widget_type == "CTkFrame" and "CTkFrame" in theme:
                config = theme["CTkFrame"]
                widget.configure(
                    fg_color=config["fg_color"][0],
                    border_color=config.get("border_color", ["white"])[0]
                )
                if "top_fg_color" in config:
                    widget.configure(top_fg_color=config["top_fg_color"][0])

            elif widget_type == "CTkButton" and "CTkButton" in theme:
                config = theme["CTkButton"]
                widget.configure(
                    fg_color=config["fg_color"],
                    hover_color=config["hover_color"],
                    text_color=config["text_color"],
                    border_color=config.get("border_color"),
                    corner_radius=config.get("corner_radius"),
                    border_width=config.get("border_width")
                )

            elif widget_type == "CTkLabel" and "CTkLabel" in theme:
                config = theme["CTkLabel"]
                widget.configure(
                    fg_color=config.get("fg_color"),
                    text_color=config["text_color"]
                )

            elif widget_type == "CTkEntry" and "CTkEntry" in theme:
                config = theme["CTkEntry"]
                widget.configure(fg_color=config["fg_color"])
            
            elif widget_type == "CTkTextbox" and "CTkTextbox" in theme:
                config = theme["CTkTextbox"]
                widget.configure(fg_color=config["fg_color"])
            
            elif widget_type == "CTkScrollbar" and "CTkScrollbar" in theme:
                config = theme["CTkScrollbar"]
                widget.configure(
                    fg_color=config["fg_color"],
                    button_color=config["button_color"],
                    button_hover_color=config["button_hover_color"],
                    corner_radius=config["corner_radius"],
                    border_spacing=config["border_spacing"]
                )
            
            elif widget_type == "CTkProgressBar" and "CTkProgressBar" in theme:
                config = theme["CTkProgressBar"]
                widget.configure(
                    fg_color=config["fg_color"],
                    border_color=config["border_color"],
                    progress_color=config["progress_color"]
                )
            
            elif widget_type == "CTkOptionMenu" and "CTkOptionMenu" in theme:
                config = theme["CTkOptionMenu"]
                widget.configure(
                    fg_color=config["fg_color"],
                    button_color=config["button_color"],
                    button_hover_color=config["button_hover_color"],
                    corner_radius=config["corner_radius"],
                    text_color=config["text_color"],
                    text_color_disabled=config["text_color_disabled"]
                )
                
            elif widget_type == "CTkCheckBox" and "CTkCheckBox" in theme:
                config = theme["CTkCheckBox"]
                widget.configure(
                    fg_color=config["fg_color"],
                    checkmark_color=config["checkmark_color"],
                    hover_color=config["hover_color"],
                    text_color=config["text_color"]
                )

            elif widget_type == "CTkRadioButton" and "CTkRadioButton" in theme:
                config = theme["CTkRadioButton"]
                widget.configure(
                    fg_color=config["fg_color"],
                    checkmark_color=config["checkmark_color"],
                    hover_color=config["hover_color"],
                    text_color=config["text_color"]
                )

            elif widget_type == "CTkSwitch" and "CTkSwitch" in theme:
                config = theme["CTkSwitch"]
                widget.configure(
                    fg_color=config["fg_color"],
                    progress_color=config["progress_color"],
                    hover_color=config["hover_color"],
                    text_color=config["text_color"]
                )

            elif widget_type == "CTkSlider" and "CTkSlider" in theme:
                config = theme["CTkSlider"]
                widget.configure(
                    fg_color=config["fg_color"],
                    progress_color=config["progress_color"],
                    button_color=config["button_color"],
                    button_hover_color=config["button_hover_color"]
                )

        except (KeyError, TypeError, AttributeError):
            # This handles cases where a specific widget type might not be 
            # fully defined in the loaded JSON theme, or the widget is a standard 
            # Tkinter widget that doesn't support these properties.
            pass
