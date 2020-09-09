import socketserver
import socket
import wx
import threading
from zeroconf import ServiceInfo, Zeroconf
from pubsub import pub

class FeatherUDPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]

        if data[0] == 0xff and data[1] == 0xff:
            x = (data[2] * 256) + data[3]
            y = (data[4] * 256) + data[5]
            pub.sendMessage('stick', x=x, y=y)
            # print(f"X: {x} Y: {y}")
            self.decodeButtons((data[6] << 8) + data[7])

    def decodeButtons(self, buttons):
        BUTTON_RIGHT = 6
        BUTTON_DOWN  = 7
        BUTTON_LEFT  = 9
        BUTTON_UP   = 10
        BUTTON_SEL  = 14
        if not buttons & (1 << BUTTON_RIGHT):
            pub.sendMessage('button', type='right', state="down")
        else: 
            pub.sendMessage('button', type='right', state="up")
        if not buttons & (1 << BUTTON_DOWN):
            pub.sendMessage('button', type='down', state="down")
        else: 
            pub.sendMessage('button', type='down', state="up")
        if not buttons & (1 << BUTTON_LEFT):
            pub.sendMessage('button', type='left', state="down")
        else: 
            pub.sendMessage('button', type='left', state="up")
        if not buttons & (1 << BUTTON_UP):
            pub.sendMessage('button', type='up', state="down")
        else: 
            pub.sendMessage('button', type='up', state="up")
        if not buttons & (1 << BUTTON_SEL):
            pub.sendMessage('button', type='sel', state="down")
        else: 
            pub.sendMessage('button', type='sel', state="up")

class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

class FeatherVisualization(wx.Frame):
    position_x = 512
    position_y = 512

    button_right = False
    button_down = False
    button_up = False
    button_left = False
    button_sel = False

    mainMenu = None

    bg_label = None
    stick_label = None
    button_left_label = None
    button_right_label = None
    button_top_label = None
    botton_down_label = None
    button_sel_label = None

    stick_image = None
    button_left_image = None
    button_right_image = None
    button_top_image = None
    botton_down_image = None
    button_sel_image = None


    def __init__(self, *args, **kw):

        super(FeatherVisualization, self).__init__(*args, **kw)

        self.panel = wx.Panel(self)
        self.png = wx.StaticBitmap(self, -1, wx.Bitmap("images/background.png", wx.BITMAP_TYPE_ANY))

        self.initLabels(self)

        pub.subscribe(self.stickListener, 'stick')
        pub.subscribe(self.buttonListener, 'button')


    def stickListener(self, x, y):
        self.stick_label.SetPosition((80 + (60/1024)*x,150 + (60/1024)*y))
    
    def buttonListener(self, type, state):
        if type == "right":
            self.button_right_label.Show(False if state == "up" else True)
        elif type == "left":
            self.button_left_label.Show(False if state == "up" else True)
        elif type == "up":
            self.button_top_label.Show(False if state == "up" else True)
        elif type == "down":
            self.button_down_label.Show(False if state == "up" else True)
        elif type == "sel":
            self.button_sel_label.Show(False if state == "up" else True)
        self.Layout()


    def initLabels(self, parent):
        self.stick_label = wx.StaticBitmap(parent, -1, wx.Bitmap("images/Joystick.png", wx.BITMAP_TYPE_ANY))
        self.stick_label.SetPosition((110,180))

        self.button_left_label = wx.StaticBitmap(parent, -1, wx.Bitmap("images/Left.png", wx.BITMAP_TYPE_ANY))
        self.button_left_label.SetPosition((488,188))
        self.button_left_label.Hide()
        self.button_right_label = wx.StaticBitmap(parent, -1, wx.Bitmap("images/Right.png", wx.BITMAP_TYPE_ANY))
        self.button_right_label.SetPosition((488,188))
        self.button_right_label.Hide()
        self.button_top_label = wx.StaticBitmap(parent, -1, wx.Bitmap("images/Top.png", wx.BITMAP_TYPE_ANY))
        self.button_top_label.SetPosition((488,188))
        self.button_top_label.Hide()
        self.button_down_label = wx.StaticBitmap(parent, -1, wx.Bitmap("images/Down.png", wx.BITMAP_TYPE_ANY))
        self.button_down_label.SetPosition((488,188))
        self.button_down_label.Hide()
        self.button_sel_label = wx.StaticBitmap(parent, -1, wx.Bitmap("images/Sel.png", wx.BITMAP_TYPE_ANY))
        self.button_sel_label.SetPosition((398,408))
        self.button_sel_label.Hide()


class App(wx.App):
    def OnExit(self):
        """Close the frame, terminating the application."""
        # self.Close(True)
        return 0

if __name__ == "__main__":

    HOST, PORT = socket.gethostbyname(socket.gethostname()), 9999

    app = App()
    vis = FeatherVisualization(None, title=f"JoyWing @ {HOST} {PORT}", size=(800,600))
    vis.Show()
    

    #Prepare the broadcast of our service 
    bonjour = Zeroconf()

    # Create the server, binding to localhost on port 9999
    with ThreadedUDPServer((HOST, PORT), FeatherUDPHandler) as server:

        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        #Now that the server is reachable
        desc = {'version': '0.10'}
        addresses = [socket.inet_aton(HOST)]
        expected = {HOST}
        if socket.has_ipv6:
            addresses.append(socket.inet_pton(socket.AF_INET6, '::1'))
            expected.add('::1')
        info = ServiceInfo(
            "_joyWing._udp.local.",
            "_JoyWing_Remote._joyWing._udp.local.",
            addresses=addresses,
            port=PORT,
            properties=desc,
        )

        bonjour.register_service(info)

        app.MainLoop()

        # When the server closes
        bonjour.unregister_service(info)
        bonjour.close
        server.shutdown()

