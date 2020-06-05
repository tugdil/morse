import telnetlib
import time


class MorseConnection:
    host = 'localhost'
    morse_port = 4000
    morse_connection = None
    message_id = None

    def __init__(self):
        self.message_id = 0
        self.connect_to_morse()

    def connect_to_morse(self):
        self.morse_connection = telnetlib.Telnet(self.host, self.morse_port)

    def morse_message(self, message):
        morse_message = 'id' + str(self.message_id) + ' ' + message
        morse_message = morse_message.encode('ascii')+b"\n"
        self.message_id += 1
        return morse_message

    def morse_write(self, message):
        self.morse_connection.write(self.morse_message(message))
        self.morse_connection.read_until(b"SUCCESS", 10)

    def stop_robot(self):
        message = 'robot.motion stop'
        self.morse_write(message)

    def move_robot(self, speed, duration):
        message = 'robot.motion set_speed [' + str(speed) + ', 0.0]'
        self.morse_write(message)
        time.sleep(duration)
        self.stop_robot()

    def turn_robot(self, speed, duration):
        message = 'robot.motion set_speed [0.0, ' + str(speed) + ']'
        self.morse_write(message)
        time.sleep(duration)
        self.stop_robot()

    def position_robot(self, position, orientation):
        message = 'simulation set_object_position ["robot", ' + str(position) + ', ' + str(orientation) + ']'
        self.morse_write(message)

    def close_connection(self):
        self.morse_connection.close()