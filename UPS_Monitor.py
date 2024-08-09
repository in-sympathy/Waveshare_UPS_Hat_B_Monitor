import smbus
import time
import os
import sys
import requests
from notifypy import Notify
import threading
import subprocess
import psutil


# Alertzy code:
#Getting Alertzy account number:
def get_account_string():
  """Checks if 'account' file exists, reads from it or prompts user for input and saves to file."""

  account = None
  if os.path.exists('account'):
    with open('account', 'r') as f:
      account = f.read().strip()
  else:
    account = input("Enter your Alertzy account key: ")
    with open('account', 'w') as f:
      f.write(account)

  return account

if __name__ == "__main__":
  account = get_account_string()
  print("Using Alertzy account key: ", account)


# create a function to send notifications
def notify(title, message, group):
   global account
   files = {
       'accountKey': (None, account),
       'title': (None, title),
       'message': (None, msg),
       'group': (None, group),	
   }
   response = requests.post('https://alertzy.app/send', files=files)
   return True
	
	
	
#INA219 code:
# Config Register (R/W)
_REG_CONFIG                 = 0x00
# SHUNT VOLTAGE REGISTER (R)
_REG_SHUNTVOLTAGE           = 0x01

# BUS VOLTAGE REGISTER (R)
_REG_BUSVOLTAGE             = 0x02

# POWER REGISTER (R)
_REG_POWER                  = 0x03

# CURRENT REGISTER (R)
_REG_CURRENT                = 0x04

# CALIBRATION REGISTER (R/W)
_REG_CALIBRATION            = 0x05

class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""
    RANGE_16V               = 0x00      # set bus voltage range to 16V
    RANGE_32V               = 0x01      # set bus voltage range to 32V (default)

class Gain:
    """Constants for ``gain``"""
    DIV_1_40MV              = 0x00      # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV              = 0x01      # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV             = 0x02      # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV             = 0x03      # shunt prog. gain set to /8, 320 mV range

class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
    ADCRES_9BIT_1S          = 0x00      #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S         = 0x01      # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S         = 0x02      # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S         = 0x03      # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S         = 0x09      # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S         = 0x0A      # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S         = 0x0B      # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S        = 0x0C      # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S        = 0x0D      # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S        = 0x0E      # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S       = 0x0F      # 12bit, 128 samples, 68.10ms

class Mode:
    """Constants for ``mode``"""
    POWERDOW                = 0x00      # power down
    SVOLT_TRIGGERED         = 0x01      # shunt voltage triggered
    BVOLT_TRIGGERED         = 0x02      # bus voltage triggered
    SANDBVOLT_TRIGGERED     = 0x03      # shunt and bus voltage triggered
    ADCOFF                  = 0x04      # ADC off
    SVOLT_CONTINUOUS        = 0x05      # shunt voltage continuous
    BVOLT_CONTINUOUS        = 0x06      # bus voltage continuous
    SANDBVOLT_CONTINUOUS    = 0x07      # shunt and bus voltage continuous


class INA219:
    def __init__(self, i2c_bus=1, addr=0x40):
        self.bus = smbus.SMBus(i2c_bus);
        self.addr = addr

        # Set chip to known config values to start
        self._cal_value = 0
        self._current_lsb = 0
        self._power_lsb = 0
        self.set_calibration_32V_2A()

    def read(self,address):
        data = self.bus.read_i2c_block_data(self.addr, address, 2)
        return ((data[0] * 256 ) + data[1])

    def write(self,address,data):
        temp = [0,0]
        temp[1] = data & 0xFF
        temp[0] =(data & 0xFF00) >> 8
        self.bus.write_i2c_block_data(self.addr,address,temp)

    def set_calibration_32V_2A(self):
        """Configures to INA219 to be able to measure up to 32V and 2A of current. Counter
           overflow occurs at 3.2A.
           ..note :: These calculations assume a 0.1 shunt ohm resistor is present
        """
        # By default we use a pretty huge range for the input voltage,
        # which probably isn't the most appropriate choice for system
        # that don't use a lot of power.  But all of the calculations
        # are shown below if you want to change the settings.  You will
        # also need to change any relevant register settings, such as
        # setting the VBUS_MAX to 16V instead of 32V, etc.

        # VBUS_MAX = 32V             (Assumes 32V, can also be set to 16V)
        # VSHUNT_MAX = 0.32          (Assumes Gain 8, 320mV, can also be 0.16, 0.08, 0.04)
        # RSHUNT = 0.1               (Resistor value in ohms)

        # 1. Determine max possible current
        # MaxPossible_I = VSHUNT_MAX / RSHUNT
        # MaxPossible_I = 3.2A

        # 2. Determine max expected current
        # MaxExpected_I = 2.0A

        # 3. Calculate possible range of LSBs (Min = 15-bit, Max = 12-bit)
        # MinimumLSB = MaxExpected_I/32767
        # MinimumLSB = 0.000061              (61uA per bit)
        # MaximumLSB = MaxExpected_I/4096
        # MaximumLSB = 0,000488              (488uA per bit)

        # 4. Choose an LSB between the min and max values
        #    (Preferrably a roundish number close to MinLSB)
        # CurrentLSB = 0.0001 (100uA per bit)
        self._current_lsb = .1  # Current LSB = 100uA per bit

        # 5. Compute the calibration register
        # Cal = trunc (0.04096 / (Current_LSB * RSHUNT))
        # Cal = 4096 (0x1000)

        self._cal_value = 4096

        # 6. Calculate the power LSB
        # PowerLSB = 20 * CurrentLSB
        # PowerLSB = 0.002 (2mW per bit)
        self._power_lsb = .002  # Power LSB = 2mW per bit

        # 7. Compute the maximum current and shunt voltage values before overflow
        #
        # Max_Current = Current_LSB * 32767
        # Max_Current = 3.2767A before overflow
        #
        # If Max_Current > Max_Possible_I then
        #    Max_Current_Before_Overflow = MaxPossible_I
        # Else
        #    Max_Current_Before_Overflow = Max_Current
        # End If
        #
        # Max_ShuntVoltage = Max_Current_Before_Overflow * RSHUNT
        # Max_ShuntVoltage = 0.32V
        #
        # If Max_ShuntVoltage >= VSHUNT_MAX
        #    Max_ShuntVoltage_Before_Overflow = VSHUNT_MAX
        # Else
        #    Max_ShuntVoltage_Before_Overflow = Max_ShuntVoltage
        # End If

        # 8. Compute the Maximum Power
        # MaximumPower = Max_Current_Before_Overflow * VBUS_MAX
        # MaximumPower = 3.2 * 32V
        # MaximumPower = 102.4W

        # Set Calibration register to 'Cal' calculated above
        self.write(_REG_CALIBRATION,self._cal_value)

        # Set Config register to take into account the settings above
        self.bus_voltage_range = BusVoltageRange.RANGE_32V
        self.gain = Gain.DIV_8_320MV
        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = self.bus_voltage_range << 13 | \
                      self.gain << 11 | \
                      self.bus_adc_resolution << 7 | \
                      self.shunt_adc_resolution << 3 | \
                      self.mode
        self.write(_REG_CONFIG,self.config)

    def getShuntVoltage_mV(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_SHUNTVOLTAGE)
        if value > 32767:
            value -= 65535
        return value * 0.01

    def getBusVoltage_V(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        self.read(_REG_BUSVOLTAGE)
        return (self.read(_REG_BUSVOLTAGE) >> 3) * 0.004

    def getCurrent_mA(self):
        value = self.read(_REG_CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb

    def getPower_W(self):
        self.write(_REG_CALIBRATION,self._cal_value)
        value = self.read(_REG_POWER)
        if value > 32767:
            value -= 65535
        return value * self._power_lsb


        
if __name__=='__main__':
	
    # Create an INA219 instance.
    ina219 = INA219(addr=0x42)
    while True:
        bus_voltage = ina219.getBusVoltage_V()             # voltage on V- (load side)
        shunt_voltage = ina219.getShuntVoltage_mV() / 1000 # voltage between V+ and V- across the shunt
        current = ina219.getCurrent_mA()                   # current in mA
        power = ina219.getPower_W()                        # power in W
        p = (bus_voltage - 6)/2.4*100
        if(p > 100):p = 100
        if(p < 0):p = 0
        
        #Checking if qbittorrent is running:
        def is_qbittorrent_running():
            # Iterate through all running processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Check if the process name matches qbittorrent-nox
                    if proc.info['name'] == 'qbittorrent-nox':
                        return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return None
        pid = is_qbittorrent_running()
        print (f"pid = {pid}")

        def kill_qbittorrent():
            if pid:
                try:
                    p = psutil.Process(pid)
                    p.terminate()  # or p.kill() to force kill
                    p.wait(timeout=5)
                    print(f"qBittorrent-nox (PID: {pid}) has been terminated.")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    print(f"Failed to kill qBittorrent-nox (PID: {pid}).")
            else:
                print("qBittorrent-nox is not running.")
                
                
        #checking if running on battery:
        if current < 0 and pid != None:
            msg = "Running on batteries. Stopping qbittorrent-nox."
            kill_qbittorrent()
            pid = 0
            #alertzy push notification:
            notify("Raspberry Pi UPS", msg, "Raspberry Pi 5")
            
            #notify-pi desktop notification
            notification = Notify()
            notification.title = "Raspberry Pi UPS"
            notification.message = msg
            notification.icon = "img/Qbittorrent_off.png"
            #notification.urgency = "critical"
            #notification.timeout = 3
            #sending notificaiton:
            notification.send(block=False)	     
            
            
        #checking if battery level is 80+% - safe to restore qbittorrent-nox            
        if current > 0 and p >= 80 and pid == None:
            msg = "Charged above 80% - restarting qbittorrent-nox"
            #alertzy push notification:
            notify("Raspberry Pi UPS", msg, "Raspberry Pi 5")						
            #notify-pi desktop notification
            notification = Notify()
            notification.title = "Raspberry Pi UPS"
            notification.message = msg
            notification.icon = "img/Qbittorrent_on.png"
            #notification.urgency = "critical"
            #notification.timeout = 3
            #sending notificaiton:
            notification.send(block=False)
            def start_qbittorrent():
                        # Use subprocess.Popen to start qbittorrent-nox
                        process = subprocess.Popen(["qbittorrent-nox"],stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        # Optionally, wait for the process to complete and capture output
                        stdout, stderr = process.communicate()
                        print(stdout.decode())
                        print(stderr.decode())

            # Create a thread to run the start_qbittorrent function
            thread = threading.Thread(target=start_qbittorrent)

            # Start the thread
            thread.start()

            # Continue with other tasks in the main thread
            print("qBittorrent-nox is running in a separate thread.")
                
        #checking battery level to initiate safe shutdown below 25%:
        if p <= 25 and p >= 20 and current < 0:
            msg = "Low battery. Shutting down in 60 seconds!"
            #alertzy push notification:
            notify("Raspberry Pi UPS", msg, "Raspberry Pi 5")
                    
            #notify-pi desktop notification
            notification = Notify()
            notification.title = "Raspberry Pi UPS"
            notification.message = msg
            notification.icon = "img/Low-Battery-Warning.jpg"
            #notification.urgency = "critical"
            #notification.timeout = 3
            #sending notificaiton:
            notification.send(block=False)		
                            
            #scheduling shutdown in 60 seconds:
            os.system("sudo shutdown -h +1")
            
            
        #checking if charging has been restored:	
        if current > 0 and p >= 35 and p <= 55:
            msg = "Charging restored. Cancelling shutdown."
            os.system("sudo shutdown -c")
            #alertzy push notification:
            notify("Raspberry Pi UPS", msg, "Raspberry Pi 5")						
            #notify-pi desktop notification
            notification = Notify()
            notification.title = "Raspberry Pi UPS"
            notification.message = msg
            notification.icon = "img/Charging.jpg"
            #notification.urgency = "critical"
            #notification.timeout = 3
            #sending notificaiton:
            notification.send(block=False)                   
                    


        # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
        #print("PSU Voltage:   {:6.3f} V".format(bus_voltage + shunt_voltage))
        #print("Shunt Voltage: {:9.6f} V".format(shunt_voltage))
        print("Load Voltage:  {:6.3f} V".format(bus_voltage))
        print("Current:       {:9.6f} A".format(current/1000))
        print("Power:         {:6.3f} W".format(power))
        print("Percent:       {:3.1f}%".format(p))
        print("")

        time.sleep(2)
	        
