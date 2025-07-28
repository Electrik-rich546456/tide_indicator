#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


# Application indicator which displays tidal information.
# The end user must write a Python3 script to obtain the tidal data.


INDICATOR_NAME = "tide"
import gettext
gettext.install( INDICATOR_NAME )

import gi
gi.require_version( "Gtk", "3.0" )
gi.require_version( "Notify", "0.7" )

from gi.repository import Gtk, Notify
from indicatorbase import IndicatorBase
from pathlib import Path

import datetime, importlib.util, json, os, sys, webbrowser


class IndicatorTide( IndicatorBase ):

    CONFIG_SHOW_AS_SUBMENUS = "showAsSubmenus"
    CONFIG_SHOW_AS_SUBMENUS_EXCEPT_FIRST_DAY = "showAsSubmenusExceptFirstDay"
    CONFIG_USER_SCRIPT_CLASS_NAME = "userScriptClassName"
    CONFIG_USER_SCRIPT_PATH_AND_FILENAME = "userScriptPathAndFilename"
    CONFIG_DURATION_DAYS = "durationDays"
    CONFIG_SEAPORT_ID = "seaportId"


    def __init__( self ):
        # --- FIX START: Initialize attributes *before* calling super().__init__() ---
        # This is necessary because IndicatorBase calls self.loadConfig() during its __init__
        # which expects these attributes to exist on the IndicatorTide object.
        self.userScript = None
        self.portName = _( "" )
        self.showAsSubMenus = False
        self.showAsSubMenusExceptFirstDay = False
        self.userScriptClassName = ""
        self.userScriptPathAndFilename = ""
        self.durationDays = 7
        self.seaportId = ""
        #Define the path to your icon file
        # Assuming 'my_tide_icon.png' is in the same directory as indicator-tide.py
        # If it's elsewhere, use its full path, e.g., Path.home() / ".indicator-tide" / "my_tide_icon.png"
        icon_path = Path(__file__).parent.parent / "indicator-tide.svg"

        # --- FIX END ---

        super().__init__(
            INDICATOR_NAME,
            version = "1.0.29",
            copyrightStartYear = 2024,
            comments = "Application indicator which displays tidal information.", 
            creditz = [ "Electrik.rich" ],
            icon = str(icon_path)
        )
        Notify.init( INDICATOR_NAME )
        self.setLabel("Test Tooltip")


    def loadConfig( self, configDict ):
        """
        Loads configuration from the provided dictionary into instance attributes.
        This method is called by IndicatorBase during initialization.
        """
        # --- START DEBUGGING PRINTS (to bypass logging issues) ---
        print( f"DEBUG: IndicatorTide.loadConfig called. Received configDict: {configDict}" )
        # --- END DEBUGGING PRINTS ---

        self.getLogging().debug( "Loading configuration." )
        self.getLogging().debug( f"Config dictionary received by loadConfig: {configDict}" ) # Keep this for if logging does work

        if configDict:
            self.showAsSubMenus = configDict.get( IndicatorTide.CONFIG_SHOW_AS_SUBMENUS, False )
            self.showAsSubMenusExceptFirstDay = configDict.get( IndicatorTide.CONFIG_SHOW_AS_SUBMENUS_EXCEPT_FIRST_DAY, False )
            self.userScriptClassName = configDict.get( IndicatorTide.CONFIG_USER_SCRIPT_CLASS_NAME, "" )
            self.userScriptPathAndFilename = configDict.get( IndicatorTide.CONFIG_USER_SCRIPT_PATH_AND_FILENAME, "" )
            self.durationDays = configDict.get( IndicatorTide.CONFIG_DURATION_DAYS, 7 )
            self.seaportId = configDict.get( IndicatorTide.CONFIG_SEAPORT_ID, "" )

        # --- START DEBUGGING PRINTS (to bypass logging issues) ---
        print( f"DEBUG: IndicatorTide.loadConfig. userScriptPathAndFilename after load: {self.userScriptPathAndFilename}" )
        # --- END DEBUGGING PRINTS ---
        self.getLogging().debug( f"User script path after loadConfig: {self.userScriptPathAndFilename}" )


    def saveConfig( self ):
        """
        Saves current instance attributes to a dictionary for persistence.
        This method is called by IndicatorBase when configuration needs to be saved.
        """
        self.getLogging().debug( "Saving configuration." )
        return {
            IndicatorTide.CONFIG_SHOW_AS_SUBMENUS : self.showAsSubMenus,
            # Corrected typo: 'showAsSubmenusExceptFirstDay' -> 'showAsSubMenusExceptFirstDay'
            IndicatorTide.CONFIG_SHOW_AS_SUBMENUS_EXCEPT_FIRST_DAY : self.showAsSubMenusExceptFirstDay,
            IndicatorTide.CONFIG_USER_SCRIPT_CLASS_NAME : self.userScriptClassName,
            IndicatorTide.CONFIG_USER_SCRIPT_PATH_AND_FILENAME : self.userScriptPathAndFilename,
            IndicatorTide.CONFIG_DURATION_DAYS : self.durationDays,
            IndicatorTide.CONFIG_SEAPORT_ID : self.seaportId
        }


    def __onDurationChanged( self, spinButton ):
        self.durationDays = spinButton.get_value_as_int()


    def buildMenu( self, menu, tidalReadings ):
        menu.prepend( Gtk.MenuItem.new_with_label( tidalReadings[ 0 ].getLocation() ) )
        # Only populate if we have data to display.
        if tidalReadings:
            self.getLogging().debug( "Populating menu." )

            #self.portName = tidalReadings[ 0 ].getLocation()

            if self.showAsSubMenus:
                self.__buildSubMenus( menu, tidalReadings )

            else:
                self.__buildFlatMenu( menu, tidalReadings )

        else:
            self.getLogging().info( "No tidal readings to display." )
            self.portName = _( "Error" )

            menuItem = Gtk.MenuItem( label = _( "No data" ) )
            menuItem.set_sensitive( False )
            menu.append( menuItem )


    def __buildFlatMenu( self, menu, tidalReadings ):
        for tide in tidalReadings:
            menuItem = Gtk.MenuItem( label = self.__formatLabel( tide ) )
            menuItem.connect( "activate", self.__onItemClicked, tide.getURL() )
            menu.append( menuItem )


    def __buildSubMenus( self, menu, tidalReadings ):
        # The current date.
        # Format in "YYYY-MM-DD" style so we can compare to tide date string.
        now = datetime.datetime.now().strftime( "%Y-%m-%d" )

        currentDay = None
        currentDayMenu = None

        # Build sub menus for each day.
        for tide in tidalReadings:
            # If this is a new day, create a new sub menu.
            if tide.getDate() != currentDay:
                currentDay = tide.getDate()

                if self.showAsSubMenusExceptFirstDay and now == tide.getDate():
                    # The first menu item will always link to the primary tide.
                    menuItem = Gtk.MenuItem( label = self.__formatLabel( tide ) )
                    menuItem.connect( "activate", self.__onItemClicked, tide.getURL() )
                    menu.append( menuItem )

                else:
                    # Create the sub menu and add an item to display the first item of tide.
                    currentDayMenu = Gtk.Menu()
                    menuItem = Gtk.MenuItem( label = tide.getDate() )
                    menuItem.set_submenu( currentDayMenu )
                    menu.append( menuItem )

                    menuItem = Gtk.MenuItem( label = self.__formatLabel( tide ) )
                    menuItem.connect( "activate", self.__onItemClicked, tide.getURL() )
                    currentDayMenu.append( menuItem )

            else:
                # Add an item to display the next item of tide.
                if self.showAsSubMenusExceptFirstDay and now == tide.getDate():
                    # The first menu item will always link to the primary tide.
                    menuItem = Gtk.MenuItem( label = self.__formatLabel( tide ) )
                    menuItem.connect( "activate", self.__onItemClicked, tide.getURL() )
                    menu.append( menuItem )

                else:
                    menuItem = Gtk.MenuItem( label = self.__formatLabel( tide ) )
                    menuItem.connect( "activate", self.__onItemClicked, tide.getURL() )
                    currentDayMenu.append( menuItem )


    def __formatLabel( self, tide ):
        if tide.isHigh():
            #pass
            #icon = "⬆"
            icon = "High"
        else:
            #pass
            icon = "Low"
            #icon = "⬇"

        return "{} ({}): {}".format( icon, tide.getTime(),  tide.getLevel() )
        #return "{} {} ({}): {}" tide.getTime(), tide.getLevel() 


    def update( self, menu ):
        # Set the default icon.
        self.indicator.set_icon_full( self.icon, self.icon )

        self.setLabel( self.portName )

        nextUpdateInSeconds = 30 * 60 # Default to 30 minutes.

        # Defensive check: If userScriptPathAndFilename is empty after init/loadConfig,
        # attempt to re-read it directly from the config file as a fallback.
        if not self.userScriptPathAndFilename:
            config_file_path = Path.home() / f".{INDICATOR_NAME}" / f"{INDICATOR_NAME}.json"
            #print(f"DEBUG: Initial userScriptPathAndFilename empty. Checking fallback at: {config_file_path}")
            if config_file_path.exists():
                try:
                    with open(config_file_path, 'r') as f:
                        direct_config = json.load(f)
                        self.userScriptPathAndFilename = direct_config.get(IndicatorTide.CONFIG_USER_SCRIPT_PATH_AND_FILENAME, "")
                        self.userScriptClassName = direct_config.get(IndicatorTide.CONFIG_USER_SCRIPT_CLASS_NAME, "") # Also load class name
                        self.durationDays = direct_config.get(IndicatorTide.CONFIG_DURATION_DAYS, 7) # Also load duration
                        self.seaportId = direct_config.get(IndicatorTide.CONFIG_SEAPORT_ID, "")

                        # Print this for debugging, even if no logs are working
                        print(f"DEBUG: Fallback config load SUCCESS: Path='{self.userScriptPathAndFilename}', Class='{self.userScriptClassName}', Duration={self.durationDays}")

                except json.JSONDecodeError as e: # Specific error for invalid JSON
                    print(f"ERROR: Config file is invalid JSON: {e}")
                    self.getLogging().error(f"Config file is invalid JSON: {e}")
                except Exception as e:
                    print(f"ERROR: Failed to read config file directly during fallback: {e}")
                    self.getLogging().error(f"Failed to read config file directly during fallback: {e}")
            else:
                print(f"DEBUG: Config file does not exist at {config_file_path}. No fallback possible.")
                self.getLogging().error("Config file does not exist")



        # If the user has changed the script path/filename, ensure it is set now.
        if self.userScriptPathAndFilename:
            if self.userScript is None:
                # Try to load the user script.
                self.userScript = self.__loadUserScript()

            if self.userScript:
                # The user script has been loaded.
                # Now try to obtain the tidal information from it.
                try:
                    tidalReadings = self.userScript.getTideData(
                        logging = self.getLogging(),
                        urlTimeoutInSeconds = IndicatorBase.URL_TIMEOUT_IN_SECONDS,
                        durationDays = self.durationDays,
                        seaportId = self.seaportId ) # Pass durationDays from preferences

                    self.buildMenu( menu, tidalReadings )

                except Exception as e:
                    self.getLogging().error( "Error getting tidal data from user script: {} | {}.\n{}".format( self.userScriptPathAndFilename, self.userScriptClassName, e ) )
                    # Defensive check for showNotification
                    if hasattr(self, 'showNotification'):
                        self.showNotification( _( "Tidal information" ), _( "Error getting tidal data from user script: {}. Check the log for details." ).format( self.userScriptPathAndFilename ) )
                    menuItem = Gtk.MenuItem( label = _( "Error getting data" ) )
                    menuItem.set_sensitive( False )
                    menu.append( menuItem )

            else:
                # The user script could not be loaded.
                menuItem = Gtk.MenuItem( label = _( "User script error" ) )
                menuItem.set_sensitive( False )
                menu.append( menuItem )

        else:
            # User script not set up.
            menuItem = Gtk.MenuItem( label = _( "User script not set" ) )
            menuItem.set_sensitive( False )
            menu.append( menuItem )

        return nextUpdateInSeconds


    def onPreferences( self, dialog ):
        # The dialog is already created and passed from the base class's __onPreferencesInternal.
        # Removed recursive call and redundant dialog property settings.

        dialog.set_default_size( 500, 300 )

        # Create a grid for the preference controls.
        grid = self.createGrid() # Use helper method from IndicatorBase
        dialog.vbox.pack_start( grid, True, True, 0 ) # Add grid to the dialog's vbox


        current_row = 0

        # Show as sub-menus.
        # Added xalign=0 for left alignment
        showAsSubMenusLabel = Gtk.Label( label = _( "Show as sub-menus?" ), xalign = 0 )
        showAsSubMenusSwitch = Gtk.Switch()
        showAsSubMenusSwitch.set_halign(Gtk.Align.END)
        showAsSubMenusSwitch.set_active( self.showAsSubMenus )
        showAsSubMenusSwitch.connect( "notify::active", self.__onShowAsSubMenusSwitched )
        grid.attach( showAsSubMenusLabel, 0, current_row, 1, 1 )
        grid.attach( showAsSubMenusSwitch, 1, current_row, 1, 1 )
        current_row += 1

        # Show as sub-menus (except for first day).
        # Added xalign=0 for left alignment
        showAsSubMenusExceptFirstDayLabel = Gtk.Label( label = _( "Show as sub-menus (except for first day)?" ), xalign = 0 )
        showAsSubMenusExceptFirstDaySwitch = Gtk.Switch()
        showAsSubMenusExceptFirstDaySwitch.set_halign(Gtk.Align.END)
        showAsSubMenusExceptFirstDaySwitch.set_active( self.showAsSubMenusExceptFirstDay )
        showAsSubMenusExceptFirstDaySwitch.connect( "notify::active", self.__onShowAsSubMenusExceptFirstDaySwitched )
        grid.attach( showAsSubMenusExceptFirstDayLabel, 0, current_row, 1, 1 )
        grid.attach( showAsSubMenusExceptFirstDaySwitch, 1, current_row, 1, 1 )
        current_row += 1

        # User script path and filename.
        userScriptPathAndFilenameLabel = Gtk.Label( label = _( "User script path and filename:" ), xalign = 0 )
        self.userScriptPathAndFilenameEntry = Gtk.Entry()
        self.userScriptPathAndFilenameEntry.set_hexpand(True)
        self.userScriptPathAndFilenameEntry.set_text( self.userScriptPathAndFilename )
        self.userScriptPathAndFilenameEntry.set_tooltip_text( _( "Enter the full path and filename of your tidal information script." ) )
        grid.attach( userScriptPathAndFilenameLabel, 0, current_row, 1, 1 )
        grid.attach( self.userScriptPathAndFilenameEntry, 1, current_row, 1, 1 )
        current_row += 1

        # User script class name.
        userScriptClassNameLabel = Gtk.Label( label = _( "User script class name:" ), xalign = 0 )
        self.userScriptClassNameEntry = Gtk.Entry()
        self.userScriptClassNameEntry.set_hexpand(True)
        self.userScriptClassNameEntry.set_text( self.userScriptClassName )
        self.userScriptClassNameEntry.set_tooltip_text( _( "Enter the name of the class in your script that implements TideDataGetterBase." ) )
        grid.attach( userScriptClassNameLabel, 0, current_row, 1, 1 )
        grid.attach( self.userScriptClassNameEntry, 1, current_row, 1, 1 )
        current_row += 1

        # Seaport ID ComboBox.
        seaportIdLabel = Gtk.Label( label = _( "Seaport:" ), xalign = 0 )
        self.seaportIdComboBox = Gtk.ComboBoxText()
        self.seaportIdComboBox.set_hexpand(True)
        grid.attach( seaportIdLabel, 0, current_row, 1, 1 )
        grid.attach( self.seaportIdComboBox, 1, current_row, 1, 1 )
        current_row += 1
        
        try:
            import requests
            stations_url = "https://admiraltyapi.azure-api.net/uktidalapi/api/V1/Stations"
            headers = {"Ocp-Apim-Subscription-Key": config.API_KEY}
            response = requests.get(stations_url, headers=headers, timeout=10)
            response.raise_for_status()
            stations_data = response.json()
            
            stations = sorted(stations_data['features'], key=lambda x: x['properties']['Name'])
            
            for station in stations:
                station_id = station['properties']['Id']
                station_name = station['properties']['Name']
                self.seaportIdComboBox.append(station_id, f"{station_name} ({station_id})")
            
            self.seaportIdComboBox.set_active_id(self.seaportId)

        except Exception as e:
            self.getLogging().error(f"Failed to fetch or process station list: {e}")
            self.seaportIdComboBox.append(self.seaportId, f"Could not load stations (ID: {self.seaportId})")
            self.seaportIdComboBox.set_active(0)


        # Duration Days (preference control)
        durationDaysLabel = Gtk.Label( label = _( "Duration (days):" ), xalign = 0 )
        self.durationDaysSpinButton = self.createSpinButton(
            initialValue = self.durationDays,
            minimumValue = 1,
            maximumValue = 30,
            stepIncrement = 1,
            pageIncrement = 7,
            toolTip = _( "Number of days for which to fetch tidal information." )
        )
        self.durationDaysSpinButton.connect( "value-changed", self.__onDurationChanged )
        grid.attach( durationDaysLabel, 0, current_row, 1, 1 )
        grid.attach( self.durationDaysSpinButton, 1, current_row, 1, 1 )
        current_row += 1


        dialog.show_all()
        response = dialog.run()


        # Update instance attributes if OK was clicked.
        # The saveConfig method will then be called by IndicatorBase to persist these.
        if response == Gtk.ResponseType.OK:
            self.showAsSubMenus = showAsSubMenusSwitch.get_active()
            self.showAsSubMenusExceptFirstDay = showAsSubMenusExceptFirstDaySwitch.get_active()
            self.userScriptClassName = self.userScriptClassNameEntry.get_text().strip()
            self.userScriptPathAndFilename = self.userScriptPathAndFilenameEntry.get_text().strip()
            self.seaportId = self.seaportIdComboBox.get_active_id()
            # self.durationDays is already updated by __onDurationChanged


            # Invalidate user script so it is reloaded with potentially new path/class name.
            self.userScript = None

        return response


    def __loadUserScript( self ):
        self.getLogging().debug( "Loading user script: {} | {}.".format( self.userScriptPathAndFilename, self.userScriptClassName ) )
        userScriptModule = None
        userScriptClass = None

        if not self.userScriptPathAndFilename:
            self.getLogging().error( "User script path and filename is empty. Cannot load script." )
            if hasattr(self, 'showNotification'):
                self.showNotification( _( "Tidal information" ), _( "User script path not set. Please set it in preferences." ) )
            return None

        userScriptPath = Path( self.userScriptPathAndFilename )
        
        # Add the script's directory to the Python path
        script_dir = str(userScriptPath.parent)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        if not userScriptPath.exists():
            self.getLogging().error( "User script file does not exist: {}".format( self.userScriptPathAndFilename ) )
            if hasattr(self, 'showNotification'):
                self.showNotification( _( "Tidal information" ), _( "User script file not found: {}. Please check path in preferences." ).format( self.userScriptPathAndFilename ) )
            return None

        try:
            # Create a module spec from the file path
            spec = importlib.util.spec_from_file_location( userScriptPath.stem, self.userScriptPathAndFilename )
            
            if spec is None:
                self.getLogging().error( "Could not create module spec for user script: {}".format( self.userScriptPathAndFilename ) )
                if hasattr(self, 'showNotification'):
                    self.showNotification( _( "Tidal information" ), _( "Could not load user script: {}. Check script file and permissions." ).format( self.userScriptPathAndFilename ) )
                return None

            # Load the module
            userScriptModule = importlib.util.module_from_spec( spec )
            # Add the module to sys.modules to prevent issues with re-importing in complex scenarios
            sys.modules[userScriptPath.stem] = userScriptModule 
            spec.loader.exec_module( userScriptModule )

            # Get the class object from the loaded module using the class name
            userScriptClass = getattr( userScriptModule, self.userScriptClassName )

            return userScriptClass # Return the class itself, not the module

        except AttributeError:
            self.getLogging().error(f"Class '{self.userScriptClassName}' not found in user script: {self.userScriptPathAndFilename}")
            if hasattr(self, 'showNotification'):
                self.showNotification(_("Tidal information"), _(f"User script class not found: {self.userScriptClassName}. Check name in preferences."))
            return None
        except Exception as e:
            self.getLogging().error( "Error loading or running user script: {} | {}.\n{}".format( self.userScriptPathAndFilename, self.userScriptClassName, e ) )
            if hasattr(self, 'showNotification'):
                self.showNotification( _( "Tidal information" ), _( "Error loading user script: {}. Check the log for details." ).format( self.userScriptPathAndFilename ) )
            return None


    def __onItemClicked( self, menuItem, url ):
        webbrowser.open_new_tab( url )


    def __onShowAsSubMenusSwitched( self, switch, active ):
        self.showAsSubMenus = switch.get_active()


    def __onShowAsSubMenusExceptFirstDaySwitched( self, switch, active ):
        self.showAsSubMenusExceptFirstDay = switch.get_active()


    def validatePreferences( self, dialog ):
        responseType = True

        if not self.userScriptPathAndFilenameEntry.get_text().strip():
            self.showMessage( dialog, _( "The user script path/filename cannot be empty." ) )
            self.userScriptPathAndFilenameEntry.grab_focus()
            responseType = False

        elif not self.userScriptClassNameEntry.get_text().strip():
            self.showMessage( dialog, _( "The user script class name cannot be empty." ) )
            self.userScriptClassNameEntry.grab_focus()
            responseType = False

        return responseType

if __name__ == "__main__":
    IndicatorTide().main()

