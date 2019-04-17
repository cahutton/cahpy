"""TODO."""

from socket import AF_INET, SHUT_RDWR, SOCK_STREAM, socket


def can_connect_to_internet():
    """TODO."""
    with socket(AF_INET, SOCK_STREAM) as test_socket:
        test_socket.settimeout(1)

        try:
            # Connect to Google's DNS server (which should be stable) using its
            # open port.
            test_socket.connect(('8.8.8.8', 53))
        except OSError:
            return False
        else:
            return True
        finally:
            test_socket.shutdown(SHUT_RDWR)
