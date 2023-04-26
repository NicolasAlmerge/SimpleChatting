import threading
import socket
from sty import fg, ef
from uuid import uuid4


# ============================== ERRORS ============================== #
class OperationFailed(Exception):
    """Failed actions."""
    def __init__(self, msg=None):
        self.msg = msg


class Forbidden(OperationFailed):
    """Forbidden actions, derived from `OperationFailed`."""


# ============================== PERMISSIONS ============================== #
class PermissionValues:
    """Represents permission values."""
    READ_MESSAGES      = 1
    SEND_MESSAGES      = 2
    KICK_MEMBERS       = 4
    BAN_MEMBERS        = 8
    CHANGE_NICKNAME    = 16
    MANAGE_NICKNAMES   = 32
    CHANGE_SETTINGS    = 64
    UPDATE_PERMISSIONS = 128
    ALL                = 255

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("class cannot be initialised.") from None


class Permissions:
    """Represents permissions."""

    __slots__ = ("_value",)

    def __init__(self, value: int = 0):
        if not isinstance(value, int):
            raise TypeError("value must be int.") from None
        if value < 0:
            raise ValueError("value must be non-negative.") from None
        if value > PermissionValues.ALL:
            raise ValueError("value must be less than or equal to {0}.".format(PermissionValues.ALL)) from None
        self._value = value
    
    @property
    def value(self) -> int:
        return self._value
    
    @classmethod
    def none(cls):
        return cls(0)
    
    @classmethod
    def all(cls):
        return cls(PermissionValues.ALL)
    
    @classmethod
    def default(cls):
        return cls(19)
    
    @classmethod
    def moderator(cls):
        return cls(63)
    
    @property
    def read_messages(self) -> bool:
        return bool(self._value >> 0 & 1)
    
    @property
    def send_messages(self) -> bool:
        return bool(self._value >> 1 & 1)
    
    @property
    def kick_members(self) -> bool:
        return bool(self._value >> 2 & 1)
    
    @property
    def ban_members(self) -> bool:
        return bool(self._value >> 3 & 1)
    
    @property
    def change_nickname(self) -> bool:
        return bool(self._value >> 4 & 1)
    
    @property
    def manage_nicknames(self) -> bool:
        return bool(self._value >> 5 & 1)
    
    @property
    def change_settings(self) -> bool:
        return bool(self._value >> 6 & 1)
    
    @property
    def update_permissions(self) -> bool:
        return bool(self._value >> 7 & 1)
    
    @property
    def all_permissions(self) -> bool:
        return self._value == PermissionValues.ALL
    
    def update(self, permission_value: int):
        if not isinstance(permission_value, int):
            raise TypeError("value must be int.") from None
        if permission_value < 0:
            raise ValueError("value must be non-negative.") from None
        if permission_value > PermissionValues.ALL:
            raise ValueError("value must be less than or equal to {0}.".format(PermissionValues.ALL)) from None
        self._value = permission_value

    def __bool__(self):
        return bool(self._value)
    
    def __eq__(self, other):
        if not isinstance(other, Permissions):
            return False
        return self._value == other._value
    
    def __le__(self, other):
        if not isinstance(other, Permissions):
            raise TypeError("cannot compare Permissions with {0}".format(other.__class__.__name__))
        return (self._value & other._value) == self._value
    
    def __ge__(self, other):
        if not isinstance(other, Permissions):
            raise TypeError("cannot compare Permissions with {0}".format(other.__class__.__name__))
        return (self._value | other._value) == self._value

    def __lt__(self, other):
        return self.__le__(other) and self._value != other._value
    
    def __gt__(self, other):
        return self.__ge__(other) and self._value != other._value


# ============================== GROUP ============================== #
class Group:
    """Represents a group."""

    __slots__ = ("_name", "_owner", "_clients", "_bans", "_default_perms", "_is_public", "_id")

    def __init__(self, name: str, owner):
        if not isinstance(name, str):
            raise TypeError("name of the group must be a string.") from None
        if not name:
            raise ValueError("name of the group cannot be empty.") from None
        if not isinstance(owner, User) or isinstance(owner, Client):
            raise TypeError("owner must be of user type.") from None

        _owner = Client(owner.name, owner.socket, self, Permissions.all())
        self._name = name
        self._owner = _owner
        self._clients = [_owner]
        self._bans = set()
        self._default_perms = Permissions.default()
        self._is_public = True
        self._id = uuid4().int
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def owner(self):
        return self._owner
    
    @property
    def clients(self) -> tuple:
        return tuple(self._clients)
    
    @property
    def bans(self) -> tuple:
        return tuple(self._bans)
    
    @property
    def default_perms(self):
        return self._default_perms
    
    @property
    def is_public(self) -> bool:
        return self._is_public
    
    @property
    def id(self) -> int:
        return self._id
    
    def get_index_of(self, socket) -> int:
        """Returns index of client."""
        for (index, cl) in enumerate(self._clients):
            if cl._socket == socket:
                return index
        return None
    
    def add(self, user):
        """Adds a user to the group. Ignored if user is already in the group."""
        if not isinstance(user, User):
            raise TypeError("user must be of type User.") from None
        if isinstance(user, Client):
            return user
        for member in self._clients:
            if member == user:
                return member
        if user.id in self._bans:
            raise Forbidden("member has been banned, and cannot be added!") from None

        member = Client(user.name, user.socket, self, self._default_perms)
        self._clients.append(member)
        return member
    
    def search_member(self, string: str) -> tuple:
        """Searchs and return a member, or `(-1, None)` if not found."""
        if not isinstance(string, str):
            raise TypeError("string must be of type string") from None
        for (index, member) in enumerate(self._clients):
            if member.nickname == string:
                return (index, member)
        return (-1, None)
    
    def change_name(self, new_name: str):
        """Changes the name of the group."""
        if not isinstance(new_name, str):
            raise TypeError("new name of the group must be a string.") from None
        if new_name == self._name:
            return
        if not new_name:
            raise ValueError("new name of the group cannot be empty.") from None
        self._name = new_name
    
    def change_default_permissions(self, new_value: int):
        """Changes the default member permissions of the group."""
        if new_value == self._default_perms.value:
            return
        self._default_perms.update(new_value)
    
    def make_public(self):
        """Marks the group as public."""
        if not self._is_public:
            self._is_public = True
    
    def make_private(self):
        """Marks the group as private."""
        if self._is_public:
            self._is_public = False
    
    def transfer_ownership(self, new_owner):
        """Changes the owner of the group."""
        if not isinstance(new_owner, Client):
            raise TypeError("new owner must be of type Client.") from None
        if self._owner == new_owner:
            return
        new_owner._permissions = Permissions.all()
        self._owner = new_owner
    
    def delete(self):
        """Deletes the group."""
        self._is_public = False
        self._id = 0
        self._name = None
        self._default_perms = None
        self._owner = None
        for member in self._clients:
            member._kill()
        self._clients.clear()
        self._bans.clear()
    
    def __bool__(self):
        return True
    
    def __eq__(self, other):
        if not isinstance(other, Group):
            return False
        return self._id == other._id
    
    def __len__(self):
        return len(self._clients)


# ============================== USER ============================== #
class User:
    """Represents a user."""

    __slots__ = ("_name", "_id", "_socket")

    def __init__(self, name: str, socket):
        if not isinstance(name, str):
            raise TypeError("name must be string.") from None
        if not name:
            raise ValueError("name cannot be empty.") from None
        self._socket = socket
        self._name = name
        self._id = uuid4().int
    
    @property
    def socket(self):
        return self._socket
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def id(self) -> int:
        return self._id
    
    def set_name(self, new_name: str):
        if not isinstance(new_name, str):
            raise TypeError("new name must be string.") from None
        if new_name == self._name:
            return
        if not new_name:
            raise ValueError("new name cannot be empty.") from None
        self._name = new_name
    
    def __bool__(self):
        return True
    
    def __eq__(self, other):
        if not isinstance(other, (Client, User)):
            return False
        return self._socket == other._socket


# ============================== MEMBERS ============================== #
class Client(User):
    """Represents a client member."""

    __slots__ = ("_group", "_permissions", "_nickname")

    def __init__(self, name: str, socket, group: Group, base_permissions: Permissions):
        if not isinstance(group, Group):
            raise TypeError("group must be of type Group.") from None
        if not isinstance(base_permissions, Permissions):
            raise TypeError("base_permissions must be of type Permissions.") from None
        
        super().__init__(name, socket)
        self._group = group
        self._permissions = base_permissions
        self._nickname = self.name
    
    @property
    def group(self):
        return self._group
    
    @property
    def permissions(self):
        return self._permissions
    
    @property
    def nickname(self) -> str:
        return self._nickname
    
    @property
    def is_owner(self) -> bool:
        return self._group.owner == self
    
    def set_permissions(self, new_value: int):
        """Sets new permissions for the member."""
        if new_value == self._permissions.value:
            return
        if self.is_owner:
            raise Forbidden("owner cannot have permissions changed.") from None
        self._permissions.update(new_value)
    
    def reset_permissions(self):
        """Resets member permissions to default group permissions."""
        if self._permissions == self._group.default_perms:
            return
        if self.is_owner:
            raise Forbidden("owner cannot have permissions reset.") from None
        self._permissions = self._group.default_perms
    
    def set_nickname(self, value: str):
        """Sets nickname."""
        if not isinstance(value, str):
            raise TypeError("value must be string.")
        if not value:
            raise ValueError("value cannot be empty.")
        if value == self._nickname:
            return
        for user in self._group.clients:
            if user._nickname == value:
                raise Forbidden("nickname already registered.")
        self._nickname = value
    
    def reset_nickname(self):
        """Resets nickname."""
        if self._nickname == self.name:
            return
        self._nickname = self.name
    
    def kick(self):
        """Kicks the member."""
        if self.is_owner:
            raise Forbidden("cannot remove owner from the group.") from None
        self._kill()
    
    def ban(self):
        """Bans the member."""
        group = self._group
        self.kick()
        group._bans.add(self._id)
    
    def send(self, message):
        """Sends a message."""
        if not message.decode("utf-8").strip():
            return
        self._socket.send(message)
    
    def _kill(self):
        """Kills client object."""
        self._group._clients.remove(self)
        self._group = None
        self._permissions = None
        self._nickname = None
        #self.socket.close()
        #self.socket = None


# ============================== SERVER ============================== #
host = "127.0.0.1"
port = 65432

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()


group: Group = None


def broadcast(message, exc=None):
    """Brodcasts a message."""
    for client in group.clients:
        if client.permissions.read_messages and (exc is None or exc != client):
            client.send(message)


def handle(socket):
    global group
    """Handles a client object."""
    while True:
        if group is None:
            break
        index = group.get_index_of(socket)
        if index is None:
            break
        client: Client = group.clients[index]
        try:
            message = socket.recv(1024)
            decoded = message.decode("utf-8").strip()
            if not decoded:
                continue
            lowered = decoded.lower()

            if lowered == "/id" or lowered.startswith("/id "):
                client.send((ef.bold + "Your id is {0}.".format(client.id) + ef.rs).encode("utf-8"))
                continue

            if lowered == "/info" or lowered.startswith("/info "):
                client.send("===============\n".encode("utf-8"))
                for cl_member in group.clients:
                    if cl_member.is_owner:
                        prefix = "  👑  "
                    elif group.default_perms < cl_member.permissions:
                        prefix = "  ⭐️  "
                    else:
                        prefix = "      "
                    client.send((prefix + ef.bold + cl_member.nickname + ef.rs + "\n").encode("utf-8"))
                client.send("===============\n\n".encode("utf-8"))
                continue
            
            if lowered == "/quit" or lowered.startswith("/quit "):
                if client.is_owner:
                    client.send((fg.red + "You cannot quit the group as you are the owner! Please transfer ownership before quitting." + fg.rs).encode("utf-8"))
                    continue
                nickname = client.nickname
                client.send("/quit".encode("utf-8"))
                client._kill()
                broadcast((fg.red + ef.bold + "{0} left the chat!".format(nickname) + ef.rs + fg.rs).encode("utf-8"))
                break

            if lowered == "/delete" or lowered.startswith("/delete "):
                if not client.is_owner:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                broadcast("/delete".encode("utf-8"))
                group.delete()
                group = None
                break

            if lowered == "/nick":
                if not client.permissions.change_nickname:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                client.send((fg.red + "Nickname cannot be empty!" + fg.rs).encode("utf-8"))
                continue

            if lowered == "/kick":
                if not client.permissions.kick_members:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                client.send((fg.red + "Nickname cannot be empty!" + fg.rs).encode("utf-8"))
                continue

            if lowered == "/ban":
                if not client.permissions.ban_members:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                client.send((fg.red + "Nickname cannot be empty!" + fg.rs).encode("utf-8"))
                continue

            if lowered == "/setperms":
                if not client.permissions.update_permissions:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                client.send((fg.red + "Number must be provided!" + fg.rs).encode("utf-8"))
                continue

            if lowered == "/setowner":
                if not client.is_owner:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                client.send((fg.red + "Nickname cannot be empty!" + fg.rs).encode("utf-8"))
                continue
            
            if lowered.startswith("/nick "):
                if not client.permissions.change_nickname:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                old_nickname = client.nickname
                new_nickname = decoded[6:]
                if not new_nickname:
                    client.send((fg.red + "Nickname cannot be empty!" + fg.rs).encode("utf-8"))
                    continue

                try:
                    client.set_nickname(new_nickname)
                except Forbidden:
                    client.send((fg.red + "Nickname is already taken by someone else!" + fg.rs).encode("utf-8"))
                    continue
                broadcast((fg.blue + ef.bold + "{0} has now changed his nickname to {1}.".format(old_nickname, new_nickname) + ef.rs + fg.rs).encode("utf-8"), client)
                client.send((fg.blue + ef.bold + "You have changed your nickname to {0}.".format(new_nickname) + ef.rs + fg.rs).encode("utf-8"))
                continue

            if lowered.startswith("/kick "):
                if not client.permissions.kick_members:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                index, member = group.search_member(decoded[6:])
                if member is None:
                    client.send((fg.red + "Member not found!" + fg.rs).encode("utf-8"))
                    continue
                if client == member:
                    client.send((fg.red + "You cannot kick yourself! Please use /quit to quit the group." + fg.rs).encode("utf-8"))
                    continue
                if member.is_owner:
                    client.send((fg.red + "Cannot kick user as they own the group!" + fg.rs).encode("utf-8"))
                    continue
                if not (member.permissions <= client.permissions):
                    client.send((fg.red + "Cannot kick user as they have permissions you do not have!" + fg.rs).encode("utf-8"))
                    continue

                nickname = member.nickname
                member.send("/kick".encode("utf-8"))
                member.kick()
                broadcast((fg.red + ef.bold + "{0} was kicked by {1}.".format(nickname, client.nickname) + ef.rs + fg.rs).encode("utf-8"))
                continue

            if lowered.startswith("/ban "):
                if not client.permissions.ban_members:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                index, member = group.search_member(decoded[5:])
                if member is None:
                    client.send((fg.red + "Member not found!" + fg.rs).encode("utf-8"))
                    continue
                if client == member:
                    client.send((fg.red + "You cannot ban yourself!" + fg.rs).encode("utf-8"))
                    continue
                if member.is_owner:
                    client.send((fg.red + "Cannot ban user as they own the group!" + fg.rs).encode("utf-8"))
                    continue
                if not (member.permissions <= client.permissions):
                    client.send((fg.red + "Cannot ban user as they have permissions you do not have!" + fg.rs).encode("utf-8"))
                    continue

                nickname = member.nickname
                member.send("/ban".encode("utf-8"))
                member.ban()
                broadcast((fg.red + ef.bold + "{0} was banned by {1}.".format(nickname, client.nickname) + ef.rs + fg.rs).encode("utf-8"))
                continue

            if lowered.startswith("/setperms "):
                if not client.permissions.update_permissions:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                try:
                    number = decoded[10:].split()[0]
                except IndexError:
                    client.send((fg.red + "No number specified!" + fg.rs).encode("utf-8"))
                    continue
                try:
                    number = int(number)
                    if number < 0 or number > PermissionValues.ALL:
                        raise ValueError
                except ValueError:
                    client.send((fg.red + "Permission value not recognised!" + fg.rs).encode("utf-8"))
                    continue
                if not (client.permissions >= Permissions(number)):
                    client.send((fg.red + "Cannot change permissions you do not have!" + fg.rs).encode("utf-8"))
                    continue
                index, member = group.search_member(decoded[(11+len(str(number))):])
                if member is None:
                    client.send((fg.red + "User not found!" + fg.rs).encode("utf-8"))
                    continue
                if client == member:
                    client.send((fg.red + "You cannot change yourself permissions!" + fg.rs).encode("utf-8"))
                    continue
                if member.is_owner:
                    client.send((fg.red + "Owner cannot be changed permissions!" + fg.rs).encode("utf-8"))
                    continue
                if not (member.permissions <= client.permissions):
                    client.send((fg.red + "Cannot set these permissions for member as they have permissions you do not have!" + fg.rs).encode("utf-8"))
                    continue
                member.set_permissions(number)
                broadcast((fg.green + ef.bold + "{0} now has permissions value {1}!".format(member.nickname, number) + ef.rs + fg.rs).encode("utf-8"))
                continue

            if lowered.startswith("/setowner "):
                if not client.is_owner:
                    client.send((fg.red + "Permission denied!" + fg.rs).encode("utf-8"))
                    continue
                index, member = group.search_member(decoded[10:])
                if member is None:
                    client.send((fg.red + "Member not found!" + fg.rs).encode("utf-8"))
                    continue
                if client == member:
                    client.send((fg.red + "Cannot transfer ownership to yourself!" + fg.rs).encode("utf-8"))
                    continue
                group.transfer_ownership(member)
                broadcast((fg.blue + ef.bold + "{0} is now the new group owner!".format(member.nickname) + ef.rs + fg.rs).encode("utf-8"), member)
                member.send((fg.blue + ef.bold + "You are now the group owner!" + ef.rs + fg.rs).encode("utf-8"))
                continue

            if lowered.startswith("/") and lowered != "/":
                client.send((fg.red + "Unknown command!" + fg.rs).encode("utf-8"))
                continue
            
            if client.permissions.send_messages:
                broadcast((fg.blue + ef.bold + client.nickname + ef.rs + fg.rs + ": " + message.decode("utf-8")).encode("utf-8"), client)
                # client.send((fg.green + "Message sent!" + fg.rs).encode("utf-8"))
                continue
            client.send((fg.red + "No permission to send messages!" + fg.rs).encode("utf-8"))
        except:
            try:
                nickname = client.nickname
                if client.is_owner:
                    broadcast("/delete".encode("utf-8"))
                    group.delete()
                    group = None
                    break
                client._kill()
                client.socket.close()
                broadcast((fg.red + ef.bold + "{0} left the chat!".format(nickname) + ef.rs + fg.rs).encode("utf-8"))
            finally:
                break


def receive():
    """Main loop."""
    global group
    while True:
        client, address = server.accept()
        print("Connected with {0}".format(str(address)))

        client.send("/nick".encode("utf-8"))
        if group is None:
            nickname = client.recv(1024).decode("utf-8")
            group = Group("Default", User(nickname, client))
            curr_client = group.owner
        else:
            while True:
                nickname = client.recv(1024).decode("utf-8")
                if not nickname.strip():
                    client.send((fg.red + "Nickname cannot be empty! Please retry!" + fg.rs).encode("utf-8"))
                    continue
                index, search = group.search_member(nickname)
                if search is None:
                    break
                client.send((fg.red + "Nickname already chosen! Please choose a different nickname!" + fg.rs).encode("utf-8"))
            try:
                curr_client = group.add(User(nickname, client))
            except Forbidden:
                client.send((fg.red + ef.bold + "You have been banned from this group and cannot rejoin it!" + ef.rs + fg.rs).encode("utf-8"))
                continue

        print("Nickname of the client is {0}".format(nickname))
        broadcast((fg.yellow + ef.bold + "{0} joined the chat!".format(nickname) + ef.rs + fg.rs).encode("utf-8"), curr_client)
        client.send((fg.green + ef.bold + "Connected to the server!" + ef.rs + fg.rs).encode("utf-8"))

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()


print("Server is listening on port {0}".format(port))
receive()
