# fix for pyinstaller packages app to avoid ReactorAlreadyInstalledError
import os, sys
from kivy.resources import resource_add_path
if "twisted.internet.reactor" in sys.modules:
    del sys.modules["twisted.internet.reactor"]

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor, protocol

from kivy.app import App
from kivy.config import Config

from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup


CODING = "utf-8"


class MyPopup(Popup):
    """Kasa reprezentuje okno popup"""
    def __init__(self, time_sec=1.5, **kwargs):
        super(MyPopup, self).__init__(**kwargs)
        # call dismiss_popup in 2 seconds
        Clock.schedule_once(self.dismiss_popup, time_sec)

    def dismiss_popup(self, dt):
        self.dismiss()


def showMsg(msg, size_x, size_y, time):
    """Tworzy informacyjne okno popup"""
    x = size_x*0.7
    y = size_y*0.7
    pop = MyPopup(title="Message",
                  content=Label(text=msg, text_size=(x, y), halign="center", valign="center", padding_y=x*0.05, padding_x=x*0.05, font_size=(x**2 + y**2) / 11**4),
                  size_hint=(None, None), size=(x, y),
                  #title_color= (0.7, 0, 0, 0.9),
                  #separator_color= (0.4, 0.4, 0.4, 1),
                  title_align="center",
                  time_sec=time)
    pop.open()



class GdcClient(protocol.Protocol):

    def connectionMade(self):
        #konstrkcja treści wiadomości autoryzacyjnej
        #servip = self.factory.app.root.ids.ip_.text
        #port = int(self.factory.app.root.ids.port_.text)
        nick = self.factory.app.root.ids.nickname_.text
        passw = self.factory.app.root.ids.password_.text
        #header
        data_len_and_passw = f"{str(len(gdc_app.tom) + len(nick.encode(CODING)) + len('auth')+2)}:{passw}"
        header_tmp = f"{data_len_and_passw:<{GdcApp.HEADER_LENGTH}}".encode(CODING)
        #data
        data_tmp = f"{gdc_app.tom}:{nick}:{'auth'}".encode(CODING)
        Clock.schedule_once(lambda x:self.transport.write(header_tmp + data_tmp), 0.1)
        Clock.schedule_once(lambda x:self.factory.app.on_connect(self.transport), 0.1)


    def dataReceived(self, data):
        self.factory.app.on_message(data)



class GdcClientFactory(protocol.ClientFactory):
    protocol = GdcClient

    def __init__(self, app):
        self.app = app



class GdcApp(App):
    HEADER_LENGTH = 25

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.servip = None
        self.port = None
        self.nick = None
        self.passw = None
        self.tom = "B" #type of message

    def connect(self):
        self.servip = self.root.ids.ip_.text.strip()
        self.port = self.root.ids.port_.text.strip()
        self.nick = self.root.ids.nickname_.text.strip()
        self.passw = self.root.ids.password_.text.strip()

        if self.isValidInitializeData(self.servip, self.port, self.nick, self.passw) == False:
            showMsg("Please fill in all inputs with valid information.", self.root_window.width, self.root_window.height, 1.5)
        else:
            self.write2file(self.servip, self.port, self.nick, self.passw)
            reactor.connectTCP(self.servip, int(self.port), GdcClientFactory(self))


    def disconnect(self):
        showMsg("disconnecting...", self.root_window.width, self.root_window.height, 1)
        if self.conn:
            self.conn.loseConnection()
            del self.conn
        self.root.current = "login"


    def send_msg(self, msg_):
        msg = msg_
        #skonstruowanie treści wiadomości
        #header
        data_len_and_passw = f"{str(len(gdc_app.tom) + len(self.nick.encode(CODING)) + len(msg)+2)}:"
        header_tmp = f"{data_len_and_passw:<{GdcApp.HEADER_LENGTH}}".encode(CODING)
        #data
        data_tmp = f"{gdc_app.tom}:{self.nick}:{msg}".encode(CODING)
        self.conn.write(header_tmp + data_tmp)


    def on_connect(self, conn):
        showMsg("connecting to: " + self.servip, self.root_window.width, self.root_window.height, 1)
        self.conn = conn
        self.root.current = "diceroom"


    def on_message(self, msg):
        #reaguję na wiadomości od serwera
        full_msg = msg.decode(CODING)
        partsOfmsg = full_msg.split()
        #jeśli wiadomość zawiera normalny wynik to lista ma 4 pola, np.: [18, Daniel:K100, = , 60]
        if len(partsOfmsg) == 4:
            temp_nick, temp_dice = partsOfmsg[1].split(":")
            self.root.ids.diceResult_.text = temp_dice + " => " + partsOfmsg[3]
            self.root.ids.nickname2_.text = temp_nick
        #jeśli wiadomość zawiera nick ze spacjami, np.: [18, Arnold, Steinhager:K100, = , 60]
        elif len(partsOfmsg) > 4:
            nick_and_dice = " ".join(partsOfmsg[1:-2]).split(":")
            self.root.ids.diceResult_.text = nick_and_dice[1] + " => " + partsOfmsg[-1]
            self.root.ids.nickname2_.text = nick_and_dice[0]
        else:
        #jeśli server wysyła flage FIN, wiadomośc wygląda tak: [10, Server:FIN]
            if partsOfmsg[1] == "Server:FIN":
                self.disconnect()


    def quit_app(self):
        """Zamyka okno programu"""
        App.get_running_app().stop()


    def write2file(self, ip, port, nick, passw):
        """zapisuję je do pliku data.log"""
        try:
            with open("data.log", "w") as f:
                f.write(f"{ip};{port};{nick};{passw}")
                f.close()
        except Exception as e:
            showMsg(f"An exception when writing to a file: {e}", self.root_window.width, self.root_window.height, 3)


    def clear_results(self):
        """Czyszczę pola wyniku i nicku"""
        self.root.ids.diceResult_.text = ""
        self.root.ids.nickname2_.text = ""


    def clear_pass(self):
        """Czyszczę pole password"""
        self.root.ids.password_.text = ""


    def checkbox_click(self, instance, value):
        """Event dla checkBoxa. Zmieniam pole TOM (type of message) S = single, B = broadcast"""
        if value is True: 
            self.tom = "S"
        else: 
            self.tom = "B"


    def loadDataFromFile(self):
        """Ładuje dane z pliku 'data.log' do zmiennych klasy"""
        try:
            with open("data.log", "r") as f:
                        self.root.ids.ip_.text, self.root.ids.port_.text, self.root.ids.nickname_.text, self.root.ids.password_.text = f.read().strip().split(";")
        except Exception as e:
            pass


    def isValidInitializeData(self, ip, port, nick, passw):
        """Weryfikuję czy wszystkie wprowadzone dane wejściowe (IP, PORT, NICK, PASSWORD) są poprawne. Zwracam bool"""
        retValue = []
        #Weryfikuję czy adres IP ma właściwy format
        are_digits = [item.isdigit() for item in ip.split(".")]
        if all(are_digits):
            are_correct_numbs = [True if int(item) >= 0 and int(item) < 255 else False for item in ip.split(".")]
            if all(are_correct_numbs):
                retValue.append(True)
            else:
                retValue.append(False)
        else:         
            retValue.append(False)
        #Weryfikuję czy port jest OK
        if len(port) != 0 and port.isdigit() and int(port)>1 and int(port)<65535:
            retValue.append(True)
        else:
            retValue.append(False)
        #Weryfikuję czy NICK nie jest pusty
        if len(nick) > 0: retValue.append(True)
        else:
            retValue.append(False)
        #Weryfikuję czy hasło nie jest puste
        if len(passw) > 0: retValue.append(True)
        else:
            retValue.append(False)
        
        return all(retValue)            


    def build(self):
        self.title = "Goblin Dice Client"
        self.loadDataFromFile()



#### Uwaga! Funkcja jest potrzebna tylko przy kompilacji do jednego pliku#####
def resourcePath():
    '''Returns path containing content - either locally or in pyinstaller tmp file'''
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS)

    return os.path.join(os.path.abspath("."))
################################################################################


if __name__ == "__main__":
    resource_add_path(resourcePath())
    
    #Config.set("graphics", "width", "600")
    #Config.set("graphics", "height", "900")
    Config.set("input", "mouse", "mouse,multitouch_on_demand")

    gdc_app = GdcApp()
    gdc_app.run()