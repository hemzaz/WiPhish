from unittest.mock import patch, mock_open
from pyric.pyw import interfaces, isinterface


@patch(
    "builtins.open",
    mock_open(
        read_data="""Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
enp12s0: 1263265923  910548    0   12    0     0          0       190 28743630  303148    0    0    0     0       0          0
    lo:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
"""
    ),
    spec=True,
)
def test_interfaces_two_interfaces():
    """Test the interfaces function when two interfaces are available."""
    assert interfaces() == ["enp12s0", "lo"]


@patch(
    "builtins.open",
    mock_open(
        read_data="""Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
"""
    ),
    spec=True,
)
def test_interfaces_no_interface():
    """Test interfaces function when no interfaces are available."""
    assert interfaces() == []


@patch(
    "builtins.open",
    mock_open(
        read_data="""Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
"""
    ),
    spec=True,
)
def test_isinterface_no_interface():
    """Test isinterfaces function when device is not an interface."""
    assert not isinterface("SomeDevice")


@patch(
    "builtins.open",
    mock_open(
        read_data="""Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
valid_interface: 1263265923  910548    0   12    0     0          0       190 28743630  303148    0    0    0     0       0          0
    lo:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
"""
    ),
    spec=True,
)
def test_isinterface_is_interface():
    """Test isinterfaces function when device is an interface."""
    assert isinterface("valid_interface")
