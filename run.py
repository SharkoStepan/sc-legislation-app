from sc_kpm import ScServer 
from config import Config 
from service import create_app 

if __name__ =="__main__":
    app =create_app ()

    try :
        server =ScServer (f"{Config .PROTOCOL_DEFAULT }://{Config .HOST_DEFAULT }:{Config .PORT_DEFAULT }")
        with server .connect ():
            app .run (debug =True ,host ='0.0.0.0',port =5000 )
    except Exception as e :
        from service .exceptions import ScServerError 
        raise ScServerError 