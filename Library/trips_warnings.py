from DigiSimPy.utils.ReportGen import LogReport, Manual
from DigiSimPy.KeyWords import *
from DigiSimPy.GENERIC.IODefinition import *
from DigiSimPy.GENERIC.VSDDefinition import *

config_path = 'C:/Users/Public/Configurations/config.yml'
yaml_file = open(config_path, 'r')

Controller_Type = int(Get_Controller_Type(comment="Read controller type from configuration"))
print("---------------------{}---------------------------------".format(Controller_Type))


def percent_speed_to_mA(speed):
    current_out = speed * ((20 - 4) / 100) + 4
    return current_out


@LogReport
def delay_to_transit_to_Loaded_State():
    unload_delay = 2

    if Controller_Type in [ARES_FS]:
        start_timer = ReadModbus(address=V4.Start_Time.Modbus_Register, comment="Reading current value of start timer")
        Wait(sec=int(start_timer) + unload_delay)
    if Controller_Type in [ARES_VS]:
        WriteChannel(channel=AI.Package_Discharge_Pressure, val=65, comment="Set PDP as 65 psi")
        MeasureTime(channel=AO.Motor_Speed_AO, condition=chn_condition.Equal, value=20, timeout_ms=300 * 1000,
                    tolerance_percent=90, comp=False, comment="Wait for motor speed reach to 100per")
        var_speed_delay = ReadModbus(address=AP.Variable_Speed_Delay.Modbus_Register,
                                     comment="Read Variable Speed delay")
        Wait(sec=int(var_speed_delay) + unload_delay)


@LogReport
def delay_to_transit_to_Ready_to_Start():
    stop_time = ReadModbus(address=AP.Unloaded_Stop_Time.Modbus_Register, comment='Read stop time')
    blower_timer = 10
    if Controller_Type in [ARES_FS, ARES_VS]:
        Wait(stop_time + blower_timer)


@LogReport
def simulate_Auto_Restart():
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    WriteModbus(address=AP.Auto_Restart_Time.Modbus_Register, val=AP.Auto_Restart_Time.Min,
                comment="Set Auto restart time to minimum ie 120sec")
    WriteModbus(address=AP.Minimum_Run_Time.Modbus_Register, val=AP.Minimum_Run_Time.Min,
                comment="Set Minimum run time to  3 minutes")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2,
                 comment="Set PDP less than Online pressure")
    SetHMI(button=BI.Btn_Start, comment="Start the Controller")
    delay_to_transit_to_Loaded_State()
    Wait(4)
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in loaded", ExpValue=SW.Running_Loaded, ActValue=ret)

    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_unload_pressure + 2,
                 comment="Set PDP greater than Offline pressure")
    # Wait(sec=AP.Minimum_Run_Time.Min, comment="Wait for minimum run time to expire")
    Wait(sec=AP.Auto_Restart_Time.Min, comment="Wait for Autorestart time to expire")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify controller is in Auto restart state", ExpValue=SW.Auto_Restart_State, ActValue=ret)


@LogReport
def set_pressure_for_load():
    var_pdp = ReadModbus(address=V4.Package_Discharge_Pressure.Modbus_Register,
                         comment="set_pressure_for_load: Reading current package discharge pressure")
    var_Load_Pressure = ReadModbus(address=V4.Load_Pressure.Modbus_Register,
                                   comment="set_pressure_for_load: Reading current offline pressure")
    var_difference = var_pdp - var_Load_Pressure
    if var_difference > 0:
        pdp = var_pdp - var_difference
        WriteChannel(channel=AI.Package_Discharge_Pressure, val=pdp - 2,
                     comment="set_pressure_for_load: Setting the value of control pressure")


@LogReport
def set_pressure_for_unload():
    var_pdp = ReadModbus(address=V4.Package_Discharge_Pressure.Modbus_Register,
                         comment="set_pressure_for_unload: Reading current package discharge pressure")
    var_Unload_Pressure = ReadModbus(address=V4.Unload_Pressure.Modbus_Register,
                                     comment="set_pressure_for_unload: Reading current offline pressure")
    var_difference = var_Unload_Pressure - var_pdp
    if var_difference > 0:
        pdp = var_pdp + var_difference
        WriteChannel(channel=AI.Package_Discharge_Pressure, val=pdp + 2,
                     comment="set_pressure_for_unload: Setting the value of control pressure")


@LogReport
def restart_controller_for_PORO():
    Power_Supply(power_state=DI_State.Close, comment="Powering OFF the controller & IO board")
    Wait(5, comment="Waiting for controller to power OFF")

    Power_Supply(power_state=DI_State.Open, comment="Powering ON the controller & IO board")
    Wait(Controller_Bootup_Time, comment="Waiting for controller to power ON")


@LogReport
def verify_high_inlet_vacuum_trips():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_100;Gov_FS_SanityTest_101;Gov_FS_SanityTest_102;",
                        Test_Case_Decription="Test  high inlet vacuum trip")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")

    Comment("######################### high inlet vacuum trip with high dust filter ON ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 10,
                 comment="Set the package discharge pressure less then load pressure")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Inlet_Filter_Monitoring.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="enable Inlet filter monitoring")
    WriteModbus(address=AP.Enable_High_Dust_Filter.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enable high dust filter")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    Wait(sec=Trips.High_Inlet_Vacuum.Loaded_Suppression_Time, comment="Wait for suppression time to expire")
    WriteChannel(channel=AI.Inlet_Vacuum, val=Trips.High_Inlet_Vacuum.High_Dust_Filter_ON_Thres + 0.2,
                 comment="Set Inlet vaccum above the threshold value")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.High_Inlet_Vacuum.Delay_Timer * 1000, comp=False, tolerance_percent=10,
                comment="Wait for warning to occur")
    Read_Event_Code(compare_with=Trips.High_Inlet_Vacuum.Alarm_code, comment="Verify Alarm code")


@LogReport
def clear_verify_high_inlet_vacuum_trips():
    WriteChannel(channel=AI.Inlet_Vacuum, val=AP.Inlet_Vacuum.Initial_Value, comment="Set Inlet vaccum to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    Wait(2)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that Trips indicator is cleared")
    SetHMI(button=BI.Btn_Reset, comment="Press Reset button")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_High_Dust_Filter.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Turn OFF high dust filter")


@LogReport
def verify_low_sump_pressure_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_103",
                        Test_Case_Decription="Test  Low sump pressure trip ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("########################### Low sump pressure trip  ############################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    Wait(sec=Trips.Low_Sump_Pressure.Loaded_Supression_Time)
    WriteChannel(channel=AI.Sump_Pressure, val=Trips.Low_Sump_Pressure.Threshold - 2,
                 comment="Set Sump pressure below threshold value")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.Low_Sump_Pressure.Delay_Timer * 1000, comp=False, tolerance_percent=10,
                comment="Wait for trip to occur")
    Read_Event_Code(compare_with=Trips.Low_Sump_Pressure.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_low_sump_pressure_trip():
    WriteChannel(channel=AI.Sump_Pressure, val=AP.Sump_Pressure.Initial_Value, comment="Set Sump pressure  to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the trip")
    Wait(2)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that Trip indicator is cleared")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)


@LogReport
def verify_high_sump_pressure_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_105;Gov_FS_SanityTest_106",
                        Test_Case_Decription="Test  high sump pressure trip ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("########################### high sump pressure trip  with Rated < 135psi ############################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Rated_Pressure.Modbus_Register, val=AP.Rated_Pressure.Initial_Value,
                comment="Set rated pressure to default value ie 100psi")
    WriteModbus(address=AP.Unload_Pressure.Modbus_Register, val=AP.Rated_Pressure.Initial_Value + 10,
                comment="Set unload pressure to max value")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    Wait(sec=Trips.High_Sump_Pressure.Loaded_Supression_Time)
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Unload_Pressure.Initial_Value + 20,
                 comment="to avoid Sep delta P trip")
    WriteChannel(channel=AI.Sump_Pressure,
                 val=AP.Rated_Pressure.Initial_Value + Trips.High_Sump_Pressure.Constant_with_Rated_Pressure + 2,
                 comment="Set Sump pressure above threshold value")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.High_Sump_Pressure.Delay_Timer * 1000, comp=False, tolerance_percent=10,
                comment="Wait for trip to occur")
    Read_Event_Code(compare_with=Trips.High_Sump_Pressure.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_high_sump_pressure_trip():
    WriteChannel(channel=AI.Sump_Pressure, val=AP.Sump_Pressure.Initial_Value, comment="Set Sump pressure  to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the trip")
    Wait(2)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that Trip indicator is cleared")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)


@LogReport
def verify_high_separator_delta_P_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_107;Gov_FS_SanityTest_108",
                        Test_Case_Decription="Test  High Separator delta P trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### High Separator delta P trip  with Dryer ON #############################")
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Enable, comment="enable dryer")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2,
                 comment="Set PDP to default")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    Wait(sec=8, comment="Wait for suppression time to expire")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=65, comment="Set PDP tp 95psi")
    WriteChannel(channel=AI.AfterCooler_Discharge_Pressure, val=68,
                 comment="set ADP as 100psi so that sep press drop greater than 25")
    WriteChannel(channel=AI.Sump_Pressure, val=99, comment="Set Sump pressure to 99psi")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=1000, tolerance_percent=10, comp=False,
                comment="Wait for Trip to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    Read_Event_Code(compare_with=Trips.High_Separator_Delta_P.Alarm_code, comment="Verify the Trip code")


@LogReport
def clear_verify_high_separator_delta_P_trip():
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Package_Discharge_Pressure.Initial_Value,
                 comment="Set PDP to default value")
    WriteChannel(channel=AI.AfterCooler_Discharge_Pressure, val=AP.AfterCooler_Discharge_Pressure.Initial_Value,
                 comment="Set ADP to default value")
    WriteChannel(channel=AI.Sump_Pressure, val=AP.Sump_Pressure.Initial_Value - 2,
                 comment="Set Sump pressure to default value")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)


@LogReport
def verify_check_motor_rotation():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_109",
                        Test_Case_Decription="Test  Check motor rotation trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment(
        "####################### Check motor rotation trip #############################")
    # restart_controller_for_PORO()
    # Wait(10)
    # SetHMI(button=BI.Btn_Reset,comment="Reset the trip")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2,
                 comment="Set PDP to default")
    WriteChannel(channel=AI.Sump_Pressure, val=Trips.Check_Motor_Rotation.Sump_Pressure_Threshold - 2,
                 comment="Set sump pressure below threshold")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=1000, comp=False, tolerance_percent=10,
                comment="Wait for trip to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Tripped state",
           ExpValue=SW.Tripped_State, ActValue=ret)
    Read_Event_Code(compare_with=Trips.Check_Motor_Rotation.Alarm_code, comment="Verify the Trip code")


@LogReport
def clear_verify_check_motor_rotation():
    WriteChannel(channel=AI.Sump_Pressure, val=AP.Sump_Pressure.Initial_Value - 2,
                 comment="Set Sump pressure to default value")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)


@LogReport
def verify_high_coolant_filter_press_drop_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_110",
                        Test_Case_Decription="Test  High Coolant Filter Pressure drop trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("###################### High Coolant Filter Pressure drop Trip ####################")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2,
                 comment="Set PDP below Load pressure")
    WriteModbus(address=AP.Enable_Coolant_Filter_Monitoring.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enable coolant filter monitoring")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    Wait(warnings.Change_Coolant_Filter.Loaded_State_Delay,
         comment="Waiting for Change coolant filter delay time for loaded state")

    WriteChannel(channel=AI.Injected_Coolant_Temperature, val=V4.Injected_Coolant_Temperature.Initial_Value + 35,
                 comment="Writing Injected Coolant temp greater than 120 DegF")

    WriteChannel(channel=AI.Coolant_Filter_Inlet_Pressure, val=V4.Coolant_Filter_Inlet_Pressure.Initial_Value,
                 comment="Writing coolant filter pressure")

    WriteChannel(channel=AI.Coolant_Filter_Outlet_Pressure, val=V4.Coolant_Filter_Outlet_Pressure.Initial_Value - 30,
                 comment="Writing coolant filter outlet pressure value such a way that coolant filter inlet pressure - coolant filter outlet pressure > 25")

    Wait(warnings.Change_Coolant_Filter.Delay_Time, comment="Waiting for Change coolant filter delay time")

    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.Energised, comment="Verifying the DO is energized")

    curr_state = ReadModbus(address=V4.Control_Status_Word.Modbus_Register,
                            comment="Reading the current value of control status word (state)")
    verify(ExpValue=SW.Running_Loaded_With_Warning, ActValue=curr_state,
           comment="Verifying that the current state is Loaded with Warning")

    Read_Event_Code(compare_with=warnings.Change_Coolant_Filter.Alarm_code,
                    comment="Verifying the alarm code for Change coolant filter warning")


@LogReport
def clear_verify_high_coolant_filter_press_drop_trip():
    WriteChannel(channel=AI.Coolant_Filter_Outlet_Pressure, val=V4.Coolant_Filter_Outlet_Pressure.Initial_Value - 40,
                 comment="Writing coolant filter outlet pressure value such a way that coolant filter inlet pressure - coolant filter outlet pressure > 35")

    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.High_Coolant_Filter_Pressure_Drop.Delay_Timer * 1000, tolerance_percent=10,
                comment="Wait for trip to occur")
    Read_Event_Code(compare_with=Trips.High_Coolant_Filter_Pressure_Drop.Alarm_code,
                    comment="Verifying the alarm code for Change coolant filter Trip")

    WriteChannel(channel=AI.Coolant_Filter_Outlet_Pressure, val=V4.Coolant_Filter_Outlet_Pressure.Initial_Value,
                 comment="Writing coolant filter outlet pressure to its initial value")

    SetHMI(button=BI.Btn_Reset, comment="Reset Button Pressed")

    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)
    WriteModbus(address=AP.Enable_Coolant_Filter_Monitoring.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disable coolant filter monitoring")


@LogReport
def verify_unit_too_cold_to_start():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_111",
                        Test_Case_Decription="Test  unit too cold to start  trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    # restart_controller_for_PORO()
    # Wait(10)
    # SetHMI(button=BI.Btn_Reset,comment="Reset the trip")
    WriteModbus(address=V4.Enable_Low_Ambient.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disabling Enable Low Ambient setpoint")

    set_pressure_for_load()

    WriteChannel(channel=AI.Airend_Discharge_Temperature, val=Trips.Unit_Too_Cold_to_Start.Threshold - 2,
                 comment="Writing Airend Discharge Temp to less than 35 F")

    SetHMI(button=BI.Btn_Start, comment="Simulating start button")

    curr_state = ReadModbus(address=V4.Control_Status_Word.Modbus_Register,
                            comment="Reading the current value of control status word (state)")

    verify(ExpValue=SW.Tripped_State, ActValue=curr_state, comment="The current state is Tripped State")

    Read_Event_Code(compare_with=Trips.Unit_Too_Cold_to_Start.Alarm_code,
                    comment="Verifying the alarm code for Unit Too Cold to start trip")

    Wait(2, comment="Wait for 2 seconds")


@LogReport
def clear_verify_unit_too_cold_to_start():
    WriteChannel(channel=AI.Airend_Discharge_Temperature, val=V4.Airend_Discharge_Temperature.Initial_Value,
                 comment="Writing Airend Discharge Temp to default value")

    SetHMI(button=BI.Btn_Reset, comment="Reset Button Pressed")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


@LogReport
def verify_high_airend_discharge_temperature_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_112;Gov_FS_SanityTest_113",
                        Test_Case_Decription="Test  High airend discharge temperature trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment(
        "####################### High airend discharge temperature trip in Ready to start state ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    delay_to_transit_to_Loaded_State()
    WriteChannel(channel=AI.Airend_Discharge_Temperature, val=Trips.High_Airend_Discharge_Temperature.Threshold + 2,
                 comment="Set Airend discharge temperature above trip  threshold limit")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.Energised,
                comment="Verify that Trip indicator is energized")
    Read_Event_Code(compare_with=Trips.High_Airend_Discharge_Temperature.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_high_airend_discharge_temperature_trip():
    WriteChannel(channel=AI.Airend_Discharge_Temperature, val=AP.Airend_Discharge_Temperature.Initial_Value,
                 comment="Set Airend discharge temperature to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


@LogReport
def verify_emergency_stop_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_114",
                        Test_Case_Decription="Test E stop trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### Emergency stop trip in Ready to start state ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)

    WriteChannel(channel=DI.Emergency_Stop, val=Trips.Emergency_Stop.DI_State_Threshold, comment="Open estop DI")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.Energised,
                comment="Verify that Trip indicator is energized")
    Read_Event_Code(compare_with=Trips.Emergency_Stop.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_emergency_stop_trip():
    WriteChannel(channel=DI.Emergency_Stop, val=DI_State.Close, comment="Close estop DI")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


@LogReport
def verify_main_motor_overload_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_115",
                        Test_Case_Decription="Test Main motor overload trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### Main motor overload trip in Ready to start state ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)

    WriteChannel(channel=DI.Main_Motor_Overload, val=Trips.Main_Motor_Overload.DI_State_Threshold,
                 comment="Open estop DI")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.Main_Motor_Overload.Delay_Timer * 1000, comp=False, tolerance_percent=10,
                comment="Wait for Trip to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    Read_Event_Code(compare_with=Trips.Main_Motor_Overload.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_main_motor_overload_trip():
    WriteChannel(channel=DI.Main_Motor_Overload, val=DI_State.Close, comment="Close main motor overload DI")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


@LogReport
def verify_Blower_Fault_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_116",
                        Test_Case_Decription="Test Blower Fault trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### Blower Fault trip  ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Blower_Control_Type.Modbus_Register, val=LB.Blower_Type.VSD,
                comment="Set blower type to VSD")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    WriteChannel(channel=DI.Fan_Motor_Overload_Blower_Fault, val=Trips.Blower_Fault.DI_State_Threshold,
                 comment=" Open Fan motor overload  DI")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.Blower_Fault.Delay_Timer * 1000, comp=False, tolerance_percent=10,
                comment="Wait for Trip to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    Read_Event_Code(compare_with=Trips.Blower_Fault.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_Blower_Fault_trip():
    WriteChannel(channel=DI.Fan_Motor_Overload_Blower_Fault, val=DI_State.Close,
                 comment="Close Fan motor overload overload DI")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)
    Wait(sec=10, comment="Wait for Isolation contact open start inhibit to clear")


@LogReport
def verify_fan_motor_overload_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_116",
                        Test_Case_Decription="Test Fan motor overload trip ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### Fan motor overload trip  ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Blower_Control_Type.Modbus_Register, val=LB.Blower_Type.Constant,
                comment="Set blower type to Constant")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    WriteChannel(channel=DI.Fan_Motor_Overload_Blower_Fault, val=Trips.Fan_Motor_Overload.DI_State_Threshold,
                 comment=" Open Fan motor overload  DI")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.Fan_Motor_Overload.Delay_Timer * 1000, comp=False, tolerance_percent=10,
                comment="Wait for Trip to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    Read_Event_Code(compare_with=Trips.Fan_Motor_Overload.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_fan_motor_overload_trip():
    WriteChannel(channel=DI.Fan_Motor_Overload_Blower_Fault, val=DI_State.Close, comment="Close fan motor overload DI")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


@LogReport
def verify_remote_stop_failure_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_118",
                        Test_Case_Decription="Test remote stop failure trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### remote stop failure trip  ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Remote_Start_Stop_Enable.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enable remote start stop")

    WriteChannel(channel=DI.Remote_Stop, val=DI_State.Open, comment="Open Remote Stop")
    WriteChannel(channel=DI.Remote_Start, val=DI_State.Close, comment="Close Remote Start")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.Energised,
                comment="Verify that Trip indicator is energized")
    Read_Event_Code(compare_with=Trips.Remote_Stop_Failure.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_remote_stop_failure_trip():
    WriteChannel(channel=DI.Remote_Stop, val=DI_State.Close, comment="Close remote stop DI")
    WriteChannel(channel=DI.Remote_Start, val=DI_State.Open, comment="Open Remote Start")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


@LogReport
def verify_remote_start_failure_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_119",
                        Test_Case_Decription="Test remote start failure trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### remote start failure trip  ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Remote_Start_Stop_Enable.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enable remote start stop")
    WriteChannel(channel=DI.Remote_Start, val=DI_State.Close, comment="Close Remote Start")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.Remote_Start_Failure.Delay_Timer * 1000, tolerance_percent=10,
                comment="Wait for trip to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.Energised,
                comment="Verify that Trip indicator is energized")
    Read_Event_Code(compare_with=Trips.Remote_Start_Failure.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_remote_start_failure_trip():
    WriteChannel(channel=DI.Remote_Start, val=DI_State.Open, comment="Open remote start DI")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


@LogReport
def verify_high_ambient_temperature_trips():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_120;Gov_FS_SanityTest_121",
                        Test_Case_Decription="Test High Ambient temp trip  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("########################### High Ambient temp trip  with High Ambient ON ########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Ambient_Monitoring.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="enable ambient temperature monitoring")
    WriteModbus(address=AP.Enable_High_Ambient.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enable high ambient setpoint")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    Wait(5, comment="Wait in Loaded state")
    WriteChannel(channel=AI.Package_Inlet_Temperature, val=Trips.High_Ambient_Temperature.High_Ambient_ON_TripThres + 5,
                 comment="Set package inlet temperature above the threshold value")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.Energised,
                comment="Verify that Trip indicator is energized")
    Read_Event_Code(compare_with=Trips.High_Ambient_Temperature.Alarm_code, comment="Verify trip code")


@LogReport
def clear_verify_high_ambient_temperature_trips():
    WriteChannel(channel=AI.Package_Inlet_Temperature, val=AP.Package_Inlet_Temperature.Initial_Value,
                 comment="Set Package inlet temperature to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the trip")
    Wait(2)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that trip indicator is cleared")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Ambient_Monitoring.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disable Ambient monitoring ")


@LogReport
def verify_phase_monitor_trip():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_122",
                        Test_Case_Decription="Test Phase monitor trip")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### Phase monitor trip in Ready to start state ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Phase_Monitor.Modbus_Register, val=Setpoint_Enable.Enable, comment="enable Phase monitor")
    WriteChannel(channel=DI.Phase_Monitor, val=Trips.Phase_Monitor.DI_State_Threshold, comment="Open Phase monitor DI")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in tripped state", ExpValue=SW.Tripped_State, ActValue=ret)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.Energised,
                comment="Verify that Trip indicator is energized")
    Read_Event_Code(compare_with=Trips.Phase_Monitor.Alarm_code, comment="Verify Trip code")


@LogReport
def clear_verify_phase_monitor_trip():
    WriteChannel(channel=DI.Phase_Monitor, val=DI_State.Close, comment="Close phase monitor DI")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


# ------------------------------------------------------starting Warnings functions--------------------------------------


@LogReport
def verify_Change_Inlet_filter_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_079;Gov_FS_SanityTest_080;",
                        Test_Case_Decription="Test Inlet filter warning")
    Comment("######################### Check inlet filter with high dust filter ON ###########################")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Inlet_Filter_Monitoring.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="enable Inlet filter monitoring")
    WriteModbus(address=AP.Enable_High_Dust_Filter.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enable high dust filter")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2,
                 comment="Set PDP less than Online pressure")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    Wait(sec=warnings.Change_Inlet_Filter.Loaded_Suppression_Time, comment="Wait for suppression time to expire")
    WriteChannel(channel=AI.Inlet_Vacuum, val=warnings.Change_Inlet_Filter.High_Dust_Filter_ON_Thres + 0.2,
                 comment="Set Inlet vaccum above the threshold value")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Change_Inlet_Filter.Delay_Time * 1000, comp=False, tolerance_percent=10,
                comment="Wait for warning to occur")
    Read_Event_Code(compare_with=warnings.Change_Inlet_Filter.Alarm_code, comment="Verify warning code")


@LogReport
def clear_verify_Change_Inlet_filter_warning():
    WriteChannel(channel=AI.Inlet_Vacuum, val=AP.Inlet_Vacuum.Initial_Value, comment="Set Inlet vaccum to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    Wait(2)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that warning indicator is cleared")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_High_Dust_Filter.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Turn OFF high dust filter")


@LogReport
def verify_High_Sump_Pressure_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_081;",
                        Test_Case_Decription="Test High sump pressure warning ")
    Comment("########################### High sump pressure warning #####################################")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Disable, comment="disable dryer")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2,
                 comment="Set PDP less than Online pressure")
    WriteModbus(address=AP.Unload_Pressure.Modbus_Register, val=AP.Rated_Pressure.Initial_Value + 10,
                comment="Set unloaded pressure to 110psi")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()

    Wait(warnings.High_Sump_Pressure.Loaded_State_Delay, comment="Waiting for 8 seconds")
    WriteChannel(channel=AI.AfterCooler_Discharge_Pressure, val=110,
                 comment="Set after cooler discharge pressure to 110psi")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=108, comment="Set PDP to 98psi")

    WriteChannel(channel=AI.Sump_Pressure, val=V4.Rated_Pressure.Initial_Value + 27,
                 comment="Writing sump pressure greater than \"Rated pressure(DesignPressure)+ 25PSI\"")

    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.Energised, comment="Verifying the DO is energized")

    curr_state = ReadModbus(address=V4.Control_Status_Word.Modbus_Register,
                            comment="Reading the current value of control status word (state)")
    verify(ExpValue=SW.Running_Loaded_With_Warning, ActValue=curr_state,
           comment="Verifying that the current state is Loaded with Warning")

    Read_Event_Code(compare_with=warnings.High_Sump_Pressure.Alarm_code,
                    comment="Verifying the alarm code for High Sump Pressure warning")


@LogReport
def clear_verify_High_Sump_Pressure_warning():
    WriteChannel(channel=AI.Sump_Pressure, val=V4.Sump_Pressure.Initial_Value - 1,
                 comment="Writing sump pressure to its initial value")

    SetHMI(button=BI.Btn_Reset, comment="Reset Button Pressed")

    curr_state = ReadModbus(address=V4.Control_Status_Word.Modbus_Register,
                            comment="Reading the current value of control status word (state)")
    verify(ExpValue=SW.Running_Loaded, ActValue=curr_state,
           comment="Verifying that the current state is Loaded")

    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)


@LogReport
def verify_change_separator_element_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_082;Gov_FS_SanityTest_083;",
                        Test_Case_Decription="Test Change separator element warning  ")
    Comment("####################### Change separator element warning  with Dryer ON #############################")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Enable, comment="enable dryer")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2, comment="Set PDP to default")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    Wait(warnings.Change_Separator_Element.Loaded_State_Delay, comment="Wait for suppression time to expire")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=95, comment="Set PDP tp 95psi")
    WriteChannel(channel=AI.Injected_Coolant_Temperature, val=warnings.Change_Separator_Element.Oil_Inj_Temp_Limit + 2,
                 comment="Set inject cool temp above 120F")
    WriteChannel(channel=AI.AfterCooler_Discharge_Pressure, val=100,
                 comment="set ADP as 100psi so that sep press drop greater than 12")
    WriteChannel(channel=AI.Sump_Pressure, val=116, comment="Set Sump pressure to 116psi")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Change_Separator_Element.Delay_Time * 1000, tolerance_percent=10, comp=False,
                comment="Wait for warning ot occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning",
           ExpValue=SW.Running_Unloaded_With_Warning, ActValue=ret)
    Read_Event_Code(compare_with=warnings.Change_Separator_Element.Alarm_code, comment="Verify the warning code")


@LogReport
def clear_verify_change_separator_element_warning():
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Package_Discharge_Pressure.Initial_Value,
                 comment="Set PDP to default value")
    WriteChannel(channel=AI.AfterCooler_Discharge_Pressure, val=AP.AfterCooler_Discharge_Pressure.Initial_Value,
                 comment="Set ADP to default value")
    WriteChannel(channel=AI.Sump_Pressure, val=AP.Sump_Pressure.Initial_Value - 2,
                 comment="Set Sump pressure to default value")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)


@LogReport
def verify_high_discharge_pressure_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_084;Gov_FS_SanityTest_085;",
                        Test_Case_Decription="Test High discharge pressure warning  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment(
        "######################## High discharge pressure warning with remote load command #########################")
    WriteChannel(channel=AI.Remote_Pressure, val=current_load_pressure - 2,
                 comment="Set remote pressure less than Online pressure")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2,
                 comment="Set package discharge pressure less than Online pressure")
    SetHMI(button=BI.Btn_Start, comment="Start the Controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in loaded State", ExpValue=SW.Running_Loaded, ActValue=ret)
    WriteChannel(channel=DI.Remote_Load_Unload_Enable, val=DI_State.Close, comment="Close Remote load unload enable DI")
    WriteChannel(channel=DI.Remote_Load_Unload, val=DI_State.Close, comment="close Remote load load  DI")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Unload_Pressure.Min + 35 + 2,
                 comment="Set PDP above max allowable offline pressure")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.High_Discharge_Pressure.Delay_Time * 1000,
                comp=False, comment="Verify that WArning indicator energizes")
    Read_Event_Code(compare_with=warnings.High_Discharge_Pressure.Alarm_code,
                    comment="Verify that High discharge pressure warning has occured in Event tab")


@LogReport
def clear_verify_high_discharge_pressure_warning():
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in unloaded State", ExpValue=SW.Running_Unloaded_With_Warning,
           ActValue=ret)
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Rated_Pressure.Initial_Value - 2,
                 comment="Set PDP below rated  pressure")
    SetHMI(button=BI.Btn_Reset, comment="Reset the Warning")
    Wait(2)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised, comment="WArning cleared")

    WriteChannel(channel=DI.Remote_Load_Unload_Enable, val=DI_State.Open, comment="Open Remote load unload enable DI")
    WriteChannel(channel=DI.Remote_Load_Unload, val=DI_State.Open, comment="Open Remote load load  DI")

    SetHMI(button=BI.Btn_Stop, comment="Stop the controller")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)


@LogReport
def verify_change_coolant_filter_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_086",
                        Test_Case_Decription="Test Change coolant filter warnings  ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("###################### Change coolant filter warnings ####################")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2,
                 comment="Set PDP below Load pressure")
    WriteModbus(address=AP.Enable_Coolant_Filter_Monitoring.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enable coolant filter monitoring")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    Wait(warnings.Change_Coolant_Filter.Loaded_State_Delay,
         comment="Waiting for Change coolant filter delay time for loaded state")

    WriteChannel(channel=AI.Injected_Coolant_Temperature, val=V4.Injected_Coolant_Temperature.Initial_Value + 35,
                 comment="Writing Injected Coolant temp greater than 120 DegF")

    WriteChannel(channel=AI.Coolant_Filter_Inlet_Pressure, val=V4.Coolant_Filter_Inlet_Pressure.Initial_Value,
                 comment="Writing coolant filter pressure")

    WriteChannel(channel=AI.Coolant_Filter_Outlet_Pressure, val=V4.Coolant_Filter_Outlet_Pressure.Initial_Value - 30,
                 comment="Writing coolant filter outlet pressure value such a way that coolant filter inlet pressure - coolant filter outlet pressure > 25")

    Wait(warnings.Change_Coolant_Filter.Delay_Time, comment="Waiting for Change coolant filter delay time")

    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.Energised, comment="Verifying the DO is energized")

    curr_state = ReadModbus(address=V4.Control_Status_Word.Modbus_Register,
                            comment="Reading the current value of control status word (state)")
    verify(ExpValue=SW.Running_Loaded_With_Warning, ActValue=curr_state,
           comment="Verifying that the current state is Loaded with Warning")

    Read_Event_Code(compare_with=warnings.Change_Coolant_Filter.Alarm_code,
                    comment="Verifying the alarm code for Change coolant filter warning")


@LogReport
def clear_verify_change_coolant_filter_warning():
    WriteChannel(channel=AI.Coolant_Filter_Outlet_Pressure, val=V4.Coolant_Filter_Outlet_Pressure.Initial_Value,
                 comment="Writing coolant filter outlet pressure to its initial value")

    SetHMI(button=BI.Btn_Reset, comment="Reset Button Pressed")

    curr_state = ReadModbus(address=V4.Control_Status_Word.Modbus_Register,
                            comment="Reading the current value of control status word (state)")
    verify(ExpValue=SW.Running_Loaded, ActValue=curr_state,
           comment="Verifying that the current state is Loaded")

    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state ", ExpValue=SW.Ready_To_Start,
           ActValue=ret)
    WriteModbus(address=AP.Enable_Coolant_Filter_Monitoring.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disable coolant filter monitoring")


@LogReport
def verify_change_HE_filter_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_087",
                        Test_Case_Decription="Test CChange HE filter warning")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("######################## Change HE filter warning ############################")
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Enable, comment="enable dryer")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2, comment="Set PDP to default")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    Wait(sec=10, comment="Wait in loaded state for 10 sec")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=91, comment="Set PDP tp 91psi")
    WriteChannel(channel=AI.AfterCooler_Discharge_Pressure, val=107, comment="set ADP as 107psi")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Change_HE_Filter.Delay_Time * 1000, tolerance_percent=10, comp=False,
                comment="Wait for warning ot occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.Change_HE_Filter.Alarm_code, comment="Verify the warning code")


@LogReport
def clear_verify_change_HE_filter_warning():
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Package_Discharge_Pressure.Initial_Value,
                 comment="Set PDP to default value")
    WriteChannel(channel=AI.AfterCooler_Discharge_Pressure, val=AP.AfterCooler_Discharge_Pressure.Initial_Value,
                 comment="Set ADP to default value")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Disable, comment="Disable dryer")


@LogReport
def verify_high_ambient_temperature_warnings():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_088;Gov_FS_SanityTest_089",
                        Test_Case_Decription="Test High Ambient temp warning ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("########################### High Ambient temp warning  with High Ambient ON ########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Ambient_Monitoring.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="enable ambient temperature monitoring")
    WriteModbus(address=AP.Enable_High_Ambient.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enable high ambient setpoint")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)

    WriteChannel(channel=AI.Package_Inlet_Temperature,
                 val=warnings.High_Ambient_Temperature.High_Ambient_ON_WarnThreshold + 5,
                 comment="Set package inlet temperature above the threshold value")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.High_Ambient_Temperature.Delay_Time * 1000, comp=False, tolerance_percent=10,
                comment="Wait for warning to occur")
    Read_Event_Code(compare_with=warnings.High_Ambient_Temperature.Alarm_code, comment="Verify warning code")


@LogReport
def clear_verify_high_ambient_temperature_warnings():
    WriteChannel(channel=AI.Package_Inlet_Temperature, val=AP.Package_Inlet_Temperature.Initial_Value,
                 comment="Set Package inlet temperature to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that warning indicator is cleared")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Ambient_Monitoring.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disable Ambient monitoring ")


@LogReport
def verify_high_airend_discharge_temperature_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_090",
                        Test_Case_Decription="Test High airend discharge temperature warning ")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("####################### High airend discharge temperature warning ###########################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    WriteChannel(channel=AI.Airend_Discharge_Temperature,
                 val=warnings.High_Airend_Disch_Temp.High_AirendDisch_Temp_WarnLimit + 2,
                 comment="Set Airend discharge temperature above warning threshold limit")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.High_Airend_Disch_Temp.Delay_Time * 1000, tolerance_percent=10,
                comment="Wait for warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Warning state", ExpValue=SW.Running_Loaded_With_Warning, ActValue=ret)
    Read_Event_Code(compare_with=warnings.High_Airend_Disch_Temp.Alarm_code, comment="Verify warning code")


@LogReport
def clear_verify_high_airend_discharge_temperature_warning():
    WriteChannel(channel=AI.Airend_Discharge_Temperature, val=AP.Airend_Discharge_Temperature.Initial_Value,
                 comment="Set Airend discharge temperature to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")


@LogReport
def verify_low_condensor_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_091",
                        Test_Case_Decription="Test Low condenser warning")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("######################## Low condenser warning #########################")
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Enable, comment="enable dryer")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2, comment="Set PDP to default")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    WriteChannel(channel=AI.Dryer_Condenser, val=warnings.Low_Condenser_Temperature.Low_Condensor_WarningThreshold - 2,
                 comment="Set condensor temp below thresold")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Low_Condenser_Temperature.Low_Condensor_WarningDelayTime * 1000,
                tolerance_percent=10, comp=False, comment="Wait for warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.Low_Condenser_Temperature.Alarm_code, comment="Verify the warning code")


@LogReport
def clear_verify_low_condensor_warning():
    WriteChannel(channel=AI.Dryer_Condenser, val=AP.Dryer_Condenser.Initial_Value,
                 comment="Set condensor temperature to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Disable, comment="Disable dryer")


@LogReport
def verify_high_condensor_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_092",
                        Test_Case_Decription="Test High condenser warning")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("########################## Verify High condenser warning #########################")
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Enable, comment="enable dryer")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2, comment="Set PDP to default")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    WriteChannel(channel=AI.Dryer_Condenser,
                 val=warnings.High_Condenser_Temperature.High_Condensor_WarningThreshold + 2,
                 comment="Set condensor temp above thresold")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.High_Condenser_Temperature.High_Condensor_WarningDelayTime * 1000,
                tolerance_percent=10, comp=False, comment="Wait for warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.High_Condenser_Temperature.Alarm_code, comment="Verify the warning code")


@LogReport
def clear_verify_high_condensor_warning():
    WriteChannel(channel=AI.Dryer_Condenser, val=AP.Dryer_Condenser.Initial_Value,
                 comment="Set condensor temperature to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Disable, comment="Disable dryer")


@LogReport
def verify_freeze_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_093",
                        Test_Case_Decription="Test freeze warning")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("################## Freeze warning ####################################")
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Enable, comment="enable dryer")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2, comment="Set PDP to default")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    WriteChannel(channel=AI.Dryer_Evaporator, val=warnings.Freeze_Warning.Freeze_Warning_LowThreshold - 2,
                 comment="Set dryer evaporator temp below thresold")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Freeze_Warning.Freeze_Warning_DelayTime * 1000, tolerance_percent=10, comp=False,
                comment="Wait for warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.Freeze_Warning.Alarm_code, comment="Verify the warning code")


@LogReport
def clear_verify_freeze_warning():
    WriteChannel(channel=AI.Dryer_Evaporator, val=AP.Dryer_Evaporator.Initial_Value,
                 comment="Set dryer evaporator temperature to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Disable, comment="Disable dryer")


@LogReport
def verify_condensate_drain_error_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_094",
                        Test_Case_Decription="Test Condensate drian error warning")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("######################## Condensate drian error warning #################################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    Wait(sec=warnings.Condensate_Drain_Error.Loaded_State_Delay, comment="Wait for 4.5min in loaded state")
    WriteChannel(channel=DI.Condensate_Drain_Error, val=warnings.Condensate_Drain_Error.Dryer_Error_Input_DI_Thresh,
                 comment="Set Condensate drain error to ON")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Condensate_Drain_Error.Drain_Error_InputCloseTime * 1000, tolerance_percent=10,
                comp=False, comment="Wait for warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.Condensate_Drain_Error.Alarm_code, comment="Verify the warning code")


@LogReport
def clear_verify_condensate_drain_error_warning():
    WriteChannel(channel=DI.Condensate_Drain_Error, val=AP.Condensate_Drain_Error.Initial_Value,
                 comment="Set Condensate drain error to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Dryer.Modbus_Register, val=Setpoint_Enable.Disable, comment="Disable dryer")


@LogReport
def verify_elevated_airend_discharge_temperature_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_095",
                        Test_Case_Decription="Test Elevated Airend discharge temperature warning")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("#################### Elevated Airend discharge temperature warning ###################")
    warnings.Elevated_Airend_Disch_Temp.Delay_Time = 1800
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    WriteChannel(channel=AI.Airend_Discharge_Temperature,
                 val=warnings.Elevated_Airend_Disch_Temp.Elevated_Airend_Warn_TempLimit + 2,
                 comment="Set airend discharge temperature above threshold")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Elevated_Airend_Disch_Temp.Delay_Time * 1000, tolerance_percent=10,
                comp=False, comment="Wait for warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.Elevated_Airend_Disch_Temp.Alarm_code, comment="Verify the warning code")


@LogReport
def clear_verify_elevated_airend_discharge_temperature_warning():
    WriteChannel(channel=AI.Airend_Discharge_Temperature, val=AP.Airend_Discharge_Temperature.Initial_Value,
                 comment="Set Airend discharge temperature  to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)


@LogReport
def verify_clean_cooler_warning():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_097",
                        Test_Case_Decription="Test  Clean cooler warning")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("############## Verify Clean cooler warning #####################")
    # restart_controller_for_PORO()
    WriteModbus(address=AP.Enable_Ambient_Monitoring.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="enable Ambient monitoring")
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=current_load_pressure - 2, comment="Set PDP to default")
    SetHMI(button=BI.Btn_Start, comment="Start controller")
    delay_to_transit_to_Loaded_State()
    WriteChannel(channel=AI.Aftercooler_Discharge_Temperature, val=173,
                 comment="Set aftercooler discharge temperature to 173F")
    WriteChannel(channel=AI.Package_Inlet_Temperature, val=132,
                 comment="Set package inlet temperature to 132F")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Clean_Cooler.Delay_Time * 1000, tolerance_percent=10, comp=False,
                comment="Wait for warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.Clean_Cooler.Alarm_code, comment="Verify the warning code")


@LogReport
def clear_verify_clean_cooler_warning():
    WriteChannel(channel=AI.Aftercooler_Discharge_Temperature, val=AP.Aftercooler_Discharge_Temperature.Initial_Value,
                 comment="Set aftercooler discharge temperature to default")
    WriteChannel(channel=AI.Package_Inlet_Temperature, val=AP.Package_Inlet_Temperature.Initial_Value,
                 comment="Set package inlet temperature to defaults")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Ambient_Monitoring.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disable Ambient monitoring setpoint")


@LogReport
def verify_low_ambient_temperature_warnings():
    set_requirement_tag(SRS_ID="2.2.1.5",
                        Test_Case_ID="Gov_FS_SanityTest_098;Gov_FS_SanityTest_099",
                        Test_Case_Decription="Test  Low ambient temperature warning")
    current_load_pressure = ReadModbus(address=AP.Load_Pressure.Modbus_Register, comment="Read current Load pressure")
    current_unload_pressure = ReadModbus(address=AP.Unload_Pressure.Modbus_Register,
                                         comment="Read current UnLoad pressure")
    Comment("############## Low ambient temperature warning  with Low Ambient OFF #####################")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Ambient_Monitoring.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="enable ambient temperature monitoring")
    WriteModbus(address=AP.Enable_Low_Ambient.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disable high ambient setpoint")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)

    WriteChannel(channel=AI.Package_Inlet_Temperature, val=warnings.Low_Ambient.Low_Amb_Temp_SetpointOFF - 2,
                 comment="Set package inlet temperature below the threshold value")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Low_Ambient.Delay_Time * 1000, comp=False, tolerance_percent=10,
                comment="Wait for warning to occur")
    Read_Event_Code(compare_with=warnings.Low_Ambient.Alarm_code, comment="Verify warning code")


@LogReport
def clear_verify_low_ambient_temperature_warnings():
    WriteChannel(channel=AI.Package_Inlet_Temperature, val=AP.Package_Inlet_Temperature.Initial_Value,
                 comment="Set Package inlet temperature to default")
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that warning indicator is cleared")
    SetHMI(button=BI.Btn_Stop, comment="Press stop button")
    delay_to_transit_to_Ready_to_Start()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Ambient_Monitoring.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disable Ambient monitoring ")


@LogReport
def verify_Auxillary_Warning_1():
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Load_Pressure.Initial_Value - 2,
                 comment="Set PDP below Load pressure")
    SetHMI(button=BI.Btn_Start, comment="Press start button")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    WriteChannel(channel=DI.Auxiliary_Warning_1, val=DI_State.Close, comment="Close Auxiliary Warning 1 DI")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised, timeout_ms=1000 * 3,
                tolerance_percent=25, comment="Wait for 3 seconds for Warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.Auxiliary_1.Alarm_code, event_type=Event_Type.Warning,
                    comment="Verify the Alarm code")


@LogReport
def clear_verify_Auxillary_Warning_1():
    WriteChannel(channel=DI.Auxiliary_Warning_1, val=DI_State.Open, comment="Open Auxiliary Warning 1 DI")
    Wait(1)
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    Wait(2)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that Auxiliary Warning 1 cleared")


@LogReport
def verify_Auxillary_Warning_2():
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Load_Pressure.Initial_Value - 2,
                 comment="Set PDP below Load pressure")
    SetHMI(button=BI.Btn_Start, comment="Press start button")
    delay_to_transit_to_Loaded_State()
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Loaded state", ExpValue=SW.Running_Loaded, ActValue=ret)
    WriteChannel(channel=DI.Auxiliary_Warning_2, val=DI_State.Close, comment="Close Auxiliary Warning 2 DI")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised, timeout_ms=1000 * 3,
                tolerance_percent=25, comment="Wait for 3 seconds for Warning to occur")
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Running loaded with Warning", ExpValue=SW.Running_Loaded_With_Warning,
           ActValue=ret)
    Read_Event_Code(compare_with=warnings.Auxiliary_2.Alarm_code, event_type=Event_Type.Warning,
                    comment="Verify the Alarm code")


@LogReport
def clear_verify_Auxillary_Warning_2():
    WriteChannel(channel=DI.Auxiliary_Warning_2, val=DI_State.Open, comment="Open Auxiliary Warning 2 DI")
    Wait(1)
    SetHMI(button=BI.Btn_Reset, comment="Reset the warning")
    Wait(2)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that Auxiliary Warning 2 cleared")


@LogReport
def Simulate_Load_Unload_cycles(Num_of_days=30, per_day_load_cycles=15, mode_of_oper=LB.Operating_Mode.Automatic):
    set_requirement_tag(SRS_ID="2.2.1.1", Test_Case_ID="Gov_FS_Sanity_023;Gov_FS_Sanity_024",
                        Test_Case_Decription="load unload operation when mode of operation is Automatic Load unload")
    WriteModbus(address=AP.Mode_Of_Operation.Modbus_Register, val=mode_of_oper,
                comment="Set mode of operation as {}".format(mode_of_oper))
    for i in range(Num_of_days):
        Comment("######################### Day {} #####################################".format(i + 1))
        ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
        verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
        WriteChannel(channel=AI.Package_Discharge_Pressure, val=10,
                     comment="Set PDP to 10psi")
        SetHMI(button=BI.Btn_Start, comment="Press start button")
        delay_to_transit_to_Loaded_State()
        for ld_cycle in range(per_day_load_cycles):
            WriteChannel(channel=AI.Package_Discharge_Pressure, val=AP.Load_Pressure.Initial_Value + 30,
                         comment="Set PDP to 110psi")
            Wait(1)

            WriteChannel(channel=AI.Package_Discharge_Pressure, val=10, comment="Set PDP to 10psi")
            ret_high = ReadModbus(address=AP.Num_Load_Cycles_High.Modbus_Register,
                                  comment="Number of Load Cycles (High Bytes)")
            ret_Low = ReadModbus(address=AP.Num_Load_Cycles_Low.Modbus_Register,
                                 comment="Number of Load cycles (Low Bytes)")
            total_LoadCycles = hex(ret_high)[2:] + hex(ret_Low)[2:]
            Comment(comment="Total Load cycles count  is {}".format(int(total_LoadCycles, 16)))

        SetHMI(button=BI.Btn_Stop, comment="Press stop button")
        delay_to_transit_to_Ready_to_Start()
        ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
        verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
        if i < Num_of_days - 1:  # for last iteration don't change clock
            Controller_clock_update(days_offset=1)
            ret = Controller_clock_read(comment="Read Controller clock")
            Comment("Date changed to {}-{}-{} {}:{}:{} ".format(ret[0], ret[1], ret[2], ret[3], ret[4], ret[5]))


@LogReport
def verify_Load_Cycle_High_Duty_W():
    Controller_clock_update(to_computer_clock=True, comment="Set back controller clock to current date and time")
    Simulate_Load_Unload_cycles(Num_of_days=30, per_day_load_cycles=16, mode_of_oper=LB.Operating_Mode.Automatic)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.Energised,
                comment="Verify that Warning indicator is Energized")
    Read_Event_Code(compare_with=warnings.Load_Cycles_High_Duty.Alarm_code,
                    comment="Verify that Load Cycle High Duty warning occured")


@LogReport
def clear_verify_Load_Cycle_High_Duty_W():
    SetHMI(button=BI.Btn_Reset, comment="Press reset button")
    Wait(2)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that Warning indicator is De-energized")
    Simulate_Load_Unload_cycles(Num_of_days=1, per_day_load_cycles=16)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that Warning indicator is DeEnergized")
    Controller_clock_update(days_offset=-1, comment="Set date to previous day")


@LogReport
def verify_Load_Cycle_Severe_W():
    Controller_clock_update(to_computer_clock=True, comment="Set back controller clock to current date and time")
    Simulate_Load_Unload_cycles(Num_of_days=30, per_day_load_cycles=25)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.Energised,
                comment="Verify that Warning indicator is Energized")
    Read_Event_Code(compare_with=warnings.Load_Cycles_Severe_Duty.Alarm_code,
                    comment="Verify that Load Cycle Severe Duty warning occured")


@LogReport
def clear_verify_Load_Cycle_Severe_W():
    SetHMI(button=BI.Btn_Reset, comment="Press reset button")
    Wait(2)
    ReadChannel(channel=DO.Warning_Output, is_channel=DO_State.DeEnergised,
                comment="Verify that Warning indicator is De-energized")


@LogReport
def verify_High_Interstage_Press_Trip():
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)
    WriteModbus(address=AP.Enable_Two_Stage.Modbus_Register, val=Setpoint_Enable.Enable, comment="Enable Two stage")
    SetHMI(button=BI.Btn_Start, comment="Start the controller")
    delay_to_transit_to_Loaded_State()
    WriteChannel(channel=AI.Interstage_Pressure, val=Trips.High_Interstage_Pressure.Threshold + 1,
                 comment="Set Interstage pressure above threshold value i.e {}".format(
                     Trips.High_Interstage_Pressure.Threshold + 1))
    Wait(Trips.High_Interstage_Pressure.Delay_Timer)
    ReadChannel(channel=DO.Trip_Output, is_channel=DO_State.Energised,
                comment="Verify that Trip indicator is Energized")
    Read_Event_Code(compare_with=Trips.High_Interstage_Pressure.Alarm_code, event_type=Event_Type.Trip,
                    comment="Verify that High Interstage pressure Trip has occured")


@LogReport
def clear_verify_High_Interstage_Press_Trip():
    WriteChannel(channel=AI.Interstage_Pressure, val=Trips.High_Interstage_Pressure.Threshold - 2,
                 comment="Set Interstage pressure below threshold value i.e {}".format(
                     Trips.High_Interstage_Pressure.Threshold - 2))
    SetHMI(button=BI.Btn_Reset, comment="Reset the Trip")
    Wait(2)
    ret = ReadModbus(address=AP.Control_Status_Word.Modbus_Register, comment="Read Controller Status")
    verify(comment="Verify that controller is in Ready to start state", ExpValue=SW.Ready_To_Start, ActValue=ret)


@LogReport
def verify_Motor_Winding_Temp_Trip(WindingTempX=1, WindingTempY=2):
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempX) + ".Modbus_Register"),
                val=Setpoint_Enable.Enable,
                comment="Enabling the Motor Winding Temp" + str(WindingTempX))
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempY) + ".Modbus_Register"),
                val=Setpoint_Enable.Enable,
                comment="Enabling the Setpoint Motor Winding Temp" + str(WindingTempY))
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempX)),
                 val=eval("AP.Motor_Winding_Temp_" + str(WindingTempX) + ".Min"),
                 comment="Write min value to Motor Winding Temp" + str(WindingTempX))
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempY)),
                 val=eval("AP.Motor_Winding_Temp_" + str(WindingTempY) + ".Min"),
                 comment="Write min value to Motor Winding Temp" + str(WindingTempY))
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.Motor_Winding_Temperature_Failure.Delay_Timer * 1000, tolerance_percent=20,
                comment="Verify that trip indicator is energized")
    Read_Event_Code(compare_with=Trips.Motor_Winding_Temperature_Failure.Alarm_code, comment="Verify the Trip code")


@LogReport
def clear_verify_Motor_Winding_Temp_Trip(WindingTempX=1, WindingTempY=2):
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempX)),
                 val=eval("AP.Motor_Winding_Temp_" + str(WindingTempX) + ".Initial_Value"),
                 comment="Write Initial value to Motor Winding Temp" + str(WindingTempX))
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempY)),
                 val=eval("AP.Motor_Winding_Temp_" + str(WindingTempY) + ".Initial_Value"),
                 comment="Write Initial value to Motor Winding Temp" + str(WindingTempY))
    SetHMI(BI.Btn_Reset, comment="Reset the Trip")
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempX) + ".Modbus_Register"),
                val=Setpoint_Enable.Disable,
                comment="Disabling the Motor Winding Temp" + str(WindingTempX))
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempY) + ".Modbus_Register"),
                val=Setpoint_Enable.Disable,
                comment="Disabling the Setpoint Motor Winding Temp" + str(WindingTempY))


@LogReport
def verify_Mtr_Bearing_Fail_Trip():
    WriteModbus(address=AP.Enable_Motor_Bearing_Temperature_1.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enabling the Motor_Bearing_Temperature_1")
    WriteModbus(address=AP.Enable_Motor_Bearing_Temperature_2.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enabling the Setpoint Motor_Bearing_Temperature 2")
    WriteChannel(AI.Motor_Bearing_Temp_1, val=AP.Motor_Bearing_Temp_1.Min,
                 comment="Write min value to Motor_Bearing_Temperature_1")
    WriteChannel(AI.Motor_Bearing_Temp_2, val=AP.Motor_Bearing_Temp_1.Min,
                 comment="Write min value to Motor_Bearing_Temperature_2")
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=Trips.Motor_Bearing_Temperature_Failure.Delay_Timer * 1000, tolerance_percent=20,
                comment="Verify that trip indicator is energized")
    Read_Event_Code(compare_with=Trips.Motor_Bearing_Temperature_Failure.Alarm_code, comment="Verify the Trip code")


@LogReport
def clear_verify_Mtr_Bearing_Fail_Trip():
    WriteChannel(AI.Motor_Bearing_Temp_1,
                 val=AP.Motor_Bearing_Temp_1.Initial_Value,
                 comment="Write min value to Motor Bearing temp 1")
    WriteChannel(AI.Motor_Bearing_Temp_2,
                 val=AP.Motor_Bearing_Temp_1.Initial_Value,
                 comment="Write min value to Motor Bearing temp 2")
    SetHMI(BI.Btn_Reset, comment="Reset the Trip")
    WriteModbus(address=AP.Enable_Motor_Bearing_Temperature_1.Modbus_Register,
                val=Setpoint_Enable.Disable,
                comment="Disabling the Motor Bearing temp 1")
    WriteModbus(address=AP.Enable_Motor_Bearing_Temperature_2.Modbus_Register,
                val=Setpoint_Enable.Disable,
                comment="Disabling the Setpoint Motor Bearing Temp 2")


@LogReport
def verify_motor_bearing_1_W():
    WriteModbus(address=V4.Enable_Motor_Bearing_Temperature_1.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enabling the setpoint")

    # generate warning
    WriteChannel(AI.Motor_Bearing_Temp_1, val=AP.Motor_Bearing_Temp_1.Min,
                 comment="Write min value to Motor_Bearing_Temperature_1")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Motor_Bear_Temp_1_Open_Fault.Delay_Time * 1000, tolerance_percent=20,
                comment="Verify that Warning indicator is energized")
    Read_Event_Code(compare_with=warnings.Motor_Bear_Temp_1_Open_Fault.Alarm_code, event_type=Event_Type.Warning,
                    comment="Verify the warning code")


@LogReport
def clear_motor_bearing_1_W():
    WriteChannel(AI.Motor_Bearing_Temp_1, val=V4.Motor_Bearing_Temp_1.Initial_Value,
                 comment="Writing back the default value")

    SetHMI(button=BI.Btn_Reset, comment="Reset the Warning")

    # Disable the setpoint
    WriteModbus(address=V4.Enable_Motor_Bearing_Temperature_1.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disabling the setpoint")


@LogReport
def verify_motor_bearing_2_W():
    WriteModbus(address=V4.Enable_Motor_Bearing_Temperature_2.Modbus_Register, val=Setpoint_Enable.Enable,
                comment="Enabling the setpoint")

    # generate warning
    WriteChannel(AI.Motor_Bearing_Temp_2, val=AP.Motor_Bearing_Temp_2.Min,
                 comment="Write min value to Motor_Bearing_Temperature_2")
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Motor_Bear_Temp_2_Open_Fault.Delay_Time * 1000, tolerance_percent=20,
                comment="Verify that Warning indicator is energized")
    Read_Event_Code(compare_with=warnings.Motor_Bear_Temp_2_Open_Fault.Alarm_code, event_type=Event_Type.Warning,
                    comment="Verify the warning code")


@LogReport
def clear_motor_bearing_2_W():
    WriteChannel(AI.Motor_Bearing_Temp_2, val=V4.Motor_Bearing_Temp_2.Initial_Value,
                 comment="Writing back the default value")

    SetHMI(button=BI.Btn_Reset, comment="Reset the Warning")

    # Disable the setpoint
    WriteModbus(address=V4.Enable_Motor_Bearing_Temperature_2.Modbus_Register, val=Setpoint_Enable.Disable,
                comment="Disabling the setpoint")


@LogReport
def verify_Motor_Winding_Temp_W(WindingTempX):  #######PAss 0 to 5
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempX) + ".Modbus_Register"),
                val=Setpoint_Enable.Enable,
                comment="Enabling the Motor Winding Temp" + str(WindingTempX))

    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempX)),
                 val=eval("AP.Motor_Winding_Temp_" + str(WindingTempX) + ".Min"),
                 comment="Write min value to Motor Winding Temp" + str(WindingTempX))

    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=warnings.Motor_Wind_Temp_Failure_0.Delay_Timer * 1000, tolerance_percent=20,
                comment="Verify that warning indicator is energized")
    Read_Event_Code(compare_with=eval("warnings.Motor_Wind_Temp_Failure_" + str(WindingTempX) + ".Alarm_code"),
                    event_type=Event_Type.Warning, comment="Verify the warning code")


@LogReport
def Clear_verify_Motor_Winding_Temp_W(WindingTempX):
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempX)),
                 val=eval("AP.Motor_Winding_Temp_" + str(WindingTempX) + ".Initial_Value"),
                 comment="Write Initial value to Motor Winding Temp" + str(WindingTempX))
    SetHMI(BI.Btn_Reset, comment="Reset the Trip")
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempX) + ".Modbus_Register"),
                val=Setpoint_Enable.Disable,
                comment="Disabling the Motor Winding Temp" + str(WindingTempX))


@LogReport
def verify_High_Motor_Winding_Temperature_W(WindingTempX):  # pass 1 to 5
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempX) + ".Modbus_Register"),
                val=Setpoint_Enable.Enable,
                comment="Enabling the Motor Winding Temp" + str(WindingTempX))
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempX)),
                 val=eval("warnings.High_Motor_Wind_Temp_" + str(WindingTempX) + ".Winding_Warning_Threshold+5"),
                 comment="Write warning value to Motor Winding Temp" + str(WindingTempX))
    MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=eval("warnings.High_Motor_Wind_Temp_" + str(WindingTempX) + ".Delay_Time") * 1000,
                tolerance_percent=30,
                comment="Verify that warning indicator is energized")
    Read_Event_Code(compare_with=eval("warnings.High_Motor_Wind_Temp_" + str(WindingTempX) + ".Alarm_code"),
                    comment="Verify the warning code", event_type=Event_Type.Warning)


@LogReport
def Clear_verify_High_Motor_Winding_Temperature_W(WindingTempX):
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempX)),
                 val=eval("AP.Motor_Winding_Temp_" + str(WindingTempX) + ".Initial_Value"),
                 comment="Write Initial value to Motor Winding Temp" + str(WindingTempX))

    SetHMI(BI.Btn_Reset, comment="Reset the warning")
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempX) + ".Modbus_Register"),
                val=Setpoint_Enable.Disable,
                comment="Disabling the Motor Winding Temp" + str(WindingTempX))


@LogReport
def verify_High_Motor_Bearing_Temperature_W(Bearing_No):  # pass 1 and 2
    if Bearing_No == 1:
        WriteChannel(AI.Motor_Bearing_Temp_1, val=warnings.High_Motor_Bear_Temp_1.Bearing_Warning_Threshold + 3,
                     comment="Write Threshold value to Motor_Bearing_Temperature_1")
        MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                    timeout_ms=warnings.High_Motor_Bear_Temp_1.Delay_Time * 1000, tolerance_percent=20,
                    comment="Verify that warning indicator is energized")
        Read_Event_Code(compare_with=warnings.High_Motor_Bear_Temp_1.Alarm_code, event_type=Event_Type.Warning,
                        comment="Verify the warning code")

    elif Bearing_No == 2:
        WriteChannel(AI.Motor_Bearing_Temp_2, val=warnings.High_Motor_Bear_Temp_2.Bearing_Warning_Threshold + 3,
                     comment="Write Threshold value to Motor_Bearing_Temperature_2")
        MeasureTime(channel=DO.Warning_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                    timeout_ms=warnings.High_Motor_Bear_Temp_2.Delay_Time * 1000, tolerance_percent=20,
                    comment="Verify that warning indicator is energized")
        Read_Event_Code(compare_with=warnings.High_Motor_Bear_Temp_2.Alarm_code, event_type=Event_Type.Warning,
                        comment="Verify the warning code")


@LogReport
def Clear_verify_High_Motor_Bearing_Temperature_W(Bearing_No):
    if Bearing_No == 1:
        WriteChannel(AI.Motor_Bearing_Temp_1,
                     val=AP.Motor_Bearing_Temp_1.Initial_Value,
                     comment="Write initial value to Motor Bearing temp 1")
        SetHMI(BI.Btn_Reset, comment="Reset the warning")
        WriteModbus(address=AP.Enable_Motor_Bearing_Temperature_1.Modbus_Register,
                    val=Setpoint_Enable.Disable,
                    comment="Disabling the Motor Bearing temp 1")
    elif Bearing_No == 2:
        WriteChannel(AI.Motor_Bearing_Temp_2,
                     val=AP.Motor_Bearing_Temp_1.Initial_Value,
                     comment="Write min value to Motor Bearing temp 2")
        SetHMI(BI.Btn_Reset, comment="Reset the warning")
        WriteModbus(address=AP.Enable_Motor_Bearing_Temperature_2.Modbus_Register,
                    val=Setpoint_Enable.Disable,
                    comment="Disabling the Setpoint Motor Bearing Temp 2")


@LogReport
def verify_High_Motor_Bearing_Temperature_T(Bearing_No):
    if Bearing_No == 1:
        WriteChannel(AI.Motor_Bearing_Temp_1, val=Trips.High_Motor_Bearing_Temperature_1.Threshold + 1,
                     comment="Write Threshold value to Motor_Bearing_Temperature_1")
        MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                    timeout_ms=Trips.High_Motor_Bearing_Temperature_1.Delay_Timer * 1000, tolerance_percent=20,
                    comment="Verify that trip indicator is energized")
        Read_Event_Code(compare_with=Trips.High_Motor_Bearing_Temperature_1.Alarm_code, comment="Verify the Trip code")

    elif Bearing_No == 2:
        WriteChannel(AI.Motor_Bearing_Temp_2, val=Trips.High_Motor_Bearing_Temperature_2.Threshold + 1,
                     comment="Write Threshold value to Motor_Bearing_Temperature_2")
        MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                    timeout_ms=Trips.High_Motor_Bearing_Temperature_2.Delay_Timer * 1000, tolerance_percent=20,
                    comment="Verify that trip indicator is energized")
        Read_Event_Code(compare_with=Trips.High_Motor_Bearing_Temperature_2.Alarm_code, comment="Verify the Trip code")


@LogReport
def Clear_verify_High_Motor_Bearing_Temperature_T(Bearing_No):
    if Bearing_No == 1:
        WriteChannel(AI.Motor_Bearing_Temp_1,
                     val=AP.Motor_Bearing_Temp_1.Initial_Value,
                     comment="Write initial value to Motor Bearing temp 1")
        SetHMI(BI.Btn_Reset, comment="Reset the Trip")
        WriteModbus(address=AP.Enable_Motor_Bearing_Temperature_1.Modbus_Register,
                    val=Setpoint_Enable.Disable,
                    comment="Disabling the Motor Bearing temp 1")

    elif Bearing_No == 2:
        WriteChannel(AI.Motor_Bearing_Temp_2,
                     val=AP.Motor_Bearing_Temp_1.Initial_Value,
                     comment="Write min value to Motor Bearing temp 2")
        SetHMI(BI.Btn_Reset, comment="Reset the Trip")
        WriteModbus(address=AP.Enable_Motor_Bearing_Temperature_2.Modbus_Register,
                    val=Setpoint_Enable.Disable,
                    comment="Disabling the Setpoint Motor Bearing Temp 2")


@LogReport
def verify_High_Motor_Winding_Temperature_T(WindingTempX):  # pass 1 to 5
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempX) + ".Modbus_Register"),
                val=Setpoint_Enable.Enable,
                comment="Enabling the Motor Winding Temp" + str(WindingTempX))
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempX)),
                 val=eval("Trips.High_Motor_Winding_Temperature_" + str(WindingTempX) + ".Threshold+2"),
                 comment="Write Trip value to Motor Winding Temp" + str(WindingTempX))
    MeasureTime(channel=DO.Trip_Output, condition=chn_condition.Equal, value=DO_State.Energised,
                timeout_ms=eval(
                    "Trips.High_Motor_Winding_Temperature_" + str(WindingTempX) + ".Delay_Timer") * 1000,
                tolerance_percent=30,
                comment="Verify that trip indicator is energized")
    Read_Event_Code(compare_with=eval("Trips.High_Motor_Winding_Temperature_" + str(WindingTempX) + ".Alarm_code"),
                    comment="Verify the Trip code")


@LogReport
def clear_verify_High_Motor_Winding_Temperature_T(WindingTempX):
    WriteChannel(eval("AI.Motor_Winding_Temp_" + str(WindingTempX)),
                 val=eval("AP.Motor_Winding_Temp_" + str(WindingTempX) + ".Initial_Value"),
                 comment="Write Initial value to Motor Winding Temp" + str(WindingTempX))

    SetHMI(BI.Btn_Reset, comment="Reset the Trip")
    WriteModbus(address=eval("V4.Enable_Motor_Winding_Temperature_" + str(WindingTempX) + ".Modbus_Register"),
                val=Setpoint_Enable.Disable,
                comment="Disabling the Motor Winding Temp" + str(WindingTempX))
