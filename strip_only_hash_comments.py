import io 
import os 
import tokenize 


SKIP_DIRS ={".git",".venv","__pycache__"}


def remove_hash_comments (source :str )->str :
    out =[]
    tokgen =tokenize .generate_tokens (io .StringIO (source ).readline )
    for tok_type ,tok_str ,start ,end ,line in tokgen :
        if tok_type ==tokenize .COMMENT :
            continue 
        out .append ((tok_type ,tok_str ))
    return tokenize .untokenize (out )


def process_file (path :str ):
    with open (path ,"r",encoding ="utf-8")as f :
        src =f .read ()
    new_src =remove_hash_comments (src )
    with open (path ,"w",encoding ="utf-8")as f :
        f .write (new_src )


def walk_project (root :str ):
    for dirpath ,dirnames ,filenames in os .walk (root ):

        dirnames [:]=[d for d in dirnames if d not in SKIP_DIRS ]
        for name in filenames :
            if name .endswith (".py"):
                process_file (os .path .join (dirpath ,name ))


if __name__ =="__main__":
    walk_project (".")
