import NIDAQmx


if __name__ == "__main__":
    """
    Test code for the NIDAQmx class.
    """

    # create the object
    obj = NIDAQmx.NIDAQmx("Dev1")

    # connect to the device
    obj.open()

    # read
    channel_analog = 0
    channel_digital = 1
    obj.analog_read(channel_analog)
    obj.digital_read(channel_digital)

    # write
    channel_analog = 0
    channel_digital = 1
    data_analog = 0.5
    data_digital = False
    obj.analog_write(channel_analog, data_analog)
    obj.digital_write(channel_digital, data_digital)

    # disconnect from the device
    obj.close()
