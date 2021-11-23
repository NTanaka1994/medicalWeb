from flask import Flask,request,jsonify,render_template,session,redirect
from werkzeug.security import generate_password_hash as gph
from werkzeug.security import check_password_hash as cph
from datetime import timedelta
import sqlite3 as sql
import secrets
import html
import os
import datetime


#ディレクトリトラバーサル対策
def is_directory_traversal(file_name):
    current_directory = os.path.abspath(os.curdir)
    requested_path = os.path.relpath(file_name, start=current_directory)
    requested_path = os.path.abspath(requested_path)
    common_prefix = os.path.commonprefix([requested_path, current_directory])
    return common_prefix != current_directory

#HTTPヘッダインジェクション
def http_deader_injection(string):
    string=string.replace("\n"," ")
    string=string.replace("\r"," ")
    return string

#データベース接続

#dbname="test.db"
#conn=sql.connect(dbname,check_same_thread=False)
#cur=conn.cursor()

#スタイルシート
css="<link rel=stylesheet type=text/css href=static/css/kata2.css>"

#JQuery
jquery="<script type=text/javascript src=http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js?ver=3.8.1></script>"

#javascriptスマホ対応
jsmart="<script src=static/js/jq.js></script>"

#患者用メニュー
f=open("menu_p.txt","r",encoding="utf-8")
menu_p=f.read()
f.close()

#医者用メニュー
f=open("menu_d.txt","r",encoding="utf-8")
menu_d=f.read()
f.close()

#看護師用メニュー
f=open("menu_n.txt","r",encoding="utf-8")
menu_n=f.read()
f.close()

#サービススタート
app = Flask(__name__)
#CORS(app,supports_credentials=True)

#セッション
#シークレットキー
app.secret_key=secrets.token_urlsafe(16)
#60分間セッションを維持
app.permanent_session_lifetime=timedelta(minutes=60)

#共通
@app.route("/")
def non():
    return redirect("login")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="GET":
        res="<form method=post action=login>"
        res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n<tr><td>ユーザ名</td><td><input required type=email name=\"name\"></td>"
        res=res+"\n<tr><td>パスワード</td><td><input required type=password name=\"pass\"></td>"
        res=res+"\n<tr><td></td><td><input type=submit value=ログイン></td>"
        res=res+"</table>"
        res=res+"</form>"
        return render_template("login.html", title="パスワードを入れてください",css=css,jquery=jquery,jsmart=jsmart,res=res)
    elif request.method=="POST":
        dbname="test.db"
        conn=sql.connect(dbname,check_same_thread=False)
        cur=conn.cursor()
        cur.execute("SELECT pass,user_id,user_name,perm FROM users where mail=?",(html.escape(request.form["name"]),))
        tmp=[]
        for col in cur:
            tmp.append(col[0])
            tmp.append(col[1])
            tmp.append(col[2])
            tmp.append(col[3])
        if cph(tmp[0],html.escape(request.form["pass"])):
            session["user_id"]=tmp[1]
            session["user_name"]=tmp[2]
            session["perm"]=tmp[3]
            conn.close()
            return redirect("home")
        else:
            conn.close()
            res="<form method=post action=login>"
            res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n<tr><td>ユーザ名</td><td><input required type=email name=\"name\"></td>"
            res=res+"\n<tr><td>パスワード</td><td><input required type=password name=\"pass\"></td>"
            res=res+"\n<tr><td></td><td><input type=submit value=ログイン></td>"
            res=res+"</table>"
            res=res+"</form>"
            return render_template("login.html", title="間違っています",css=css,jquery=jquery,jsmart=jsmart,res=res)
    
@app.route("/ajax")
def ajax():
    if "perm" in session:
        if session["perm"]==1:
            dbname="test.db"
            conn=sql.connect(dbname,check_same_thread=False)
            cur=conn.cursor()
            cur.execute("SELECT user_name,user_id FROM users WHERE perm=3")
            res="<div id=\"ajaxreload\"><table border=1 align=center style=\"border-collapse: collapse\">\n"
            res=res+"\t<tr><td align=center>患者名</td><td align=center>カルテ</td><td align=center>治療方針</td><td align=center>連絡</td><td align=center>検査結果</td><td align=center>退院</td></tr>\n"
            for col in cur:
                res=res+"<tr><td align=center>"+html.escape(str(col[0]))+"</td>"
                res=res+"<td align=center><form action=record-add method=POST><input type=hidden name=id value="+str(col[1])+"><input type=submit value=追加></form></td>"
                res=res+"<td align=center><form action=treat-add method=POST><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=追加></form></td>"
                res=res+"<td align=center><form action=msg-doc method=POST><input type=hidden value="+str(col[1])+" name=user_id><input type=submit value=追加></form></td>"
                res=res+"<td align=center><form action=result-add method=POST><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=追加></form></td>"
                res=res+"<td align=center><form action=ret method=POST><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=記録></form></td></tr>\n"
            res=res+"</table>"
            cur.execute("SELECT nurse_id,title,time,msg FROM msgnur ORDER BY time DESC")
            res=res+"<h3 align=center>看護師からの連絡</h3>"
            res=res+"<table border=1 align=center style=\"border-collapse: collapse\">\n"
            for col in cur:
                cur2=conn.cursor()
                cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                for col2 in cur2:
                    res=res+"\t<tr><td>記入者</td><td>タイトル</td><td rowspan=2>記入時刻</td><td rowspan=2>"+col[2][0:19]+"</td></tr>"
                    res=res+"\t<tr><td>"+html.escape(col2[0])+"</td><td>"+col[1]+"</td></tr>"
                    res=res+"\t<tr><td colspan=4><pre>"+col[3]+"<pre></td></tr>"
            res=res+"</table></div>"
            conn.close()
            return res
        elif session["perm"]==2:
            dbname="test.db"
            conn=sql.connect(dbname,check_same_thread=False)
            cur=conn.cursor()
            cur.execute("SELECT user_name,user_id FROM users WHERE perm=3")
            res="<div id=\"ajaxreload\"><table border=1 align=center style=\"border-collapse: collapse\">\n"
            res=res+"\t<tr><td align=center>患者名</td><td align=center>ナースコール</td><td align=center>カルテ閲覧</td><td align=center>治療内容閲覧</td><td align=center>検査結果一覧</td><td align=center>患者データ</td></tr>"
            for col in cur:
                res=res+"\t<tr>"
                res=res+"<td align=center>"+html.escape(col[0])+"</td>"
                res=res+"<td align=center><form method=POST action=call><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=記録></form></td>"
                res=res+"<td align=center><form method=POST action=record-info><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=閲覧></form></td>"
                res=res+"<td align=center><form method=POST action=treat-info><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=閲覧></form></td>"
                res=res+"<td align=center><form method=POST action=result-add><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=記録></form></td>"
                res=res+"<td align=center><form method=POST action=patient><input type=hidden name=id value="+str(col[1])+"><input type=submit value=閲覧></form></td>"
                res=res+"</tr>\n"
            res=res+"</table>\n</div>"
            conn.close()
            return res
        elif session["perm"]==3:
            dbname="test.db"
            conn=sql.connect(dbname,check_same_thread=False)
            cur=conn.cursor()
            cur.execute("SELECT title_id,title,doc_id,time,msg FROM msgdoc WHERE pati_id=? ORDER BY time DESC",(int(session["user_id"]),))
            res="<div id=\"ajaxreload\"><table border=1 align=center style=\"border-collapse: collapse\">\n"
            for col in cur:
                cur2=conn.cursor()
                cur2.execute("SELECT user_name FROM users WHERE user_id=? ORDER BY time DESC",(int(col[2]),))
                for col2 in cur2:
                    res=res+"\t<tr><td>記入者</td><td>タイトル</td><td rowspan=2>記入時刻</td><td rowspan=2>"+col[3][0:19]+"</td></tr>"
                    res=res+"\t<tr><td>"+html.escape(col2[0])+"</td><td>"+col[1]+"</td></tr>"
                    res=res+"\t<tr><td colspan=4><pre>"+col[4]+"<pre></td></tr>"
            res=res+"</table></div>"
            conn.close()
            return res

@app.route("/home")
def home():
    if "perm" in session:
        if session["perm"]==1:
            dbname="test.db"
            conn=sql.connect(dbname,check_same_thread=False)
            cur=conn.cursor()
            cur.execute("SELECT user_name,user_id FROM users WHERE perm=3")
            res="<div id=\"ajaxreload\"><table border=1 align=center style=\"border-collapse: collapse\">\n"
            res=res+"\t<tr><td align=center>患者名</td><td align=center>カルテ</td><td align=center>治療方針</td><td align=center>連絡</td><td align=center>検査結果</td><td align=center>退院</td></tr>\n"
            for col in cur:
                res=res+"<tr><td align=center>"+html.escape(str(col[0]))+"</td>"
                res=res+"<td align=center><form action=record-add method=POST><input type=hidden name=id value="+str(col[1])+"><input type=submit value=追加></form></td>"
                res=res+"<td align=center><form action=treat-add method=POST><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=追加></form></td>"
                res=res+"<td align=center><form action=msg-doc method=POST><input type=hidden value="+str(col[1])+" name=user_id><input type=submit value=追加></form></td>"
                res=res+"<td align=center><form action=result-add method=POST><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=追加></form></td>"
                res=res+"<td align=center><form action=ret method=POST><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=記録></form></td></tr>\n"
            res=res+"</table>"
            cur.execute("SELECT nurse_id,title,time,msg FROM msgnur ORDER BY time DESC")
            res=res+"<h3 align=center>看護師からの連絡</h3>"
            res=res+"<table border=1 align=center style=\"border-collapse: collapse\">\n"
            for col in cur:
                cur2=conn.cursor()
                cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                for col2 in cur2:
                    res=res+"\t<tr><td>記入者</td><td>タイトル</td><td rowspan=2>記入時刻</td><td rowspan=2>"+col[2][0:19]+"</td></tr>"
                    res=res+"\t<tr><td>"+html.escape(col2[0])+"</td><td>"+col[1]+"</td></tr>"
                    res=res+"\t<tr><td colspan=4><pre>"+col[3]+"<pre></td></tr>"
            res=res+"</table></div>"
            conn.close()
            return render_template("home_medi.html", title="ホーム画面",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d,res=res)
        elif session["perm"]==2:
            dbname="test.db"
            conn=sql.connect(dbname,check_same_thread=False)
            cur=conn.cursor()
            cur.execute("SELECT user_name,user_id FROM users WHERE perm=3")
            res="<div id=\"ajaxreload\"><table border=1 align=center style=\"border-collapse: collapse\">\n"
            res=res+"\t<tr><td align=center>患者名</td><td align=center>ナースコール</td><td align=center>カルテ閲覧</td><td align=center>治療内容閲覧</td><td align=center>検査結果一覧</td><td align=center>患者データ</td></tr>"
            for col in cur:
                res=res+"\t<tr>"
                res=res+"<td align=center>"+html.escape(col[0])+"</td>"
                res=res+"<td align=center><form method=POST action=call><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=記録></form></td>"
                res=res+"<td align=center><form method=POST action=record-info><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=閲覧></form></td>"
                res=res+"<td align=center><form method=POST action=treat-info><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=閲覧></form></td>"
                res=res+"<td align=center><form method=POST action=result-add><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=記録></form></td>"
                res=res+"<td align=center><form method=POST action=patient><input type=hidden name=id value="+str(col[1])+"><input type=submit value=閲覧></form></td>"
                res=res+"</tr>\n"
            res=res+"</table>\n</div>"
            conn.close()
            return render_template("home_medi.html", title="ホーム画面",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n,res=res)
        elif session["perm"]==3:
            dbname="test.db"
            conn=sql.connect(dbname,check_same_thread=False)
            cur=conn.cursor()
            cur.execute("SELECT title_id,title,doc_id,time,msg FROM msgdoc WHERE pati_id=? ORDER BY time DESC",(int(session["user_id"]),))
            res="<h2 align=center>医者からの連絡</h2><div id=\"ajaxreload\"><table border=1 align=center style=\"border-collapse: collapse\">\n"
            for col in cur:
                cur2=conn.cursor()
                cur2.execute("SELECT user_name FROM users WHERE user_id=? ORDER BY time DESC",(int(col[2]),))
                for col2 in cur2:
                    res=res+"\t<tr><td>記入者</td><td>タイトル</td><td rowspan=2>記入時刻</td><td rowspan=2>"+col[3][0:19]+"</td></tr>"
                    res=res+"\t<tr><td>"+html.escape(col2[0])+"</td><td>"+col[1]+"</td></tr>"
                    res=res+"\t<tr><td colspan=4><pre>"+col[4]+"<pre></td></tr>"
            res=res+"</table></div>"
            conn.close()
            return render_template("home_pati.html",user_id=session["user_id"], res=res,title="ホーム画面",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
    else:
        return redirect("login")
    
#患者
@app.route("/chco",methods=["GET","POST"])
def chco():
    if "perm" in session:
        if session["perm"]==3:
            if request.method=="GET":
                token=secrets.token_hex()
                session["chco_in"]=token
                res="<form method=POST action=chco>\n"
                res=res+"<input type=hidden name=chco_in value=\""+token+"\">"
                res=res+"<table border=1 align=center style=\"border-collapse: collapse\">\n"
                res=res+"\t<tr><td>持病名</td><td><input type=text name=disa placeholder=分からない場合は不明と書いてください required></td></tr>"
                res=res+"\t<tr><td colspan=2><textarea name=cont required></textarea></td></tr>\n"
                res=res+"\t<tr><td colspan=2 align=right><input type=submit value=送信></td></tr>\n"
                res=res+"</table>\n</form>"
                return render_template("news.html", res=res,title="持病登録画面",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
            elif request.method=="POST":
                if session["chco_in"]==request.form["chco_in"]:
                    disa=request.form["disa"]
                    cont=request.form["cont"]
                    token=secrets.token_hex()
                    session["chco"]=token
                    res="<form method=POST action=chco-comp><table border=1 align=center style=\"border-collapse: collapse\">\n"
                    res=res+"\t<tr><td>持病名</td><td>"+html.escape(disa)+"</td></tr>"
                    res=res+"\t<tr><td colspan=2><pre>"+html.escape(cont)+"</pre></td></tr>\n"
                    res=res+"\t<tr><td colspan=2 align=right><input type=submit value=登録><a href=chco>登録画面に戻る</a></td></tr>\n"
                    res=res+"<input type=hidden name=disa value=\""+html.escape(disa)+"\">"
                    res=res+"<input type=hidden name=cont value=\""+html.escape(cont)+"\">"
                    res=res+"<input type=hidden name=chco value=\""+token+"\">"
                    res=res+"</table></form>"
                    return render_template("news.html", res=res,title="以下の内容で登録しますか？",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
                else:
                    return redirect("chco")
        else:
            return redirect("home")
    else:
        return redirect("login")
    
@app.route("/chco-comp",methods=["GET","POST"])
def chco_comp():
    if "perm" in session:
        if session["perm"]==3:
            if request.method=="GET":
                return redirect("chco")
            elif request.method=="POST":
                if session["chco"]==request.form["chco"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    disa=request.form["disa"]
                    cont=request.form["cont"]
                    t=(session["user_id"],cont,disa)
                    cur.execute("INSERT INTO chro (pati_id,cont,title) VALUES (?,?,?)",t)
                    conn.commit()
                    conn.close()
                    return render_template("news.html", title="登録しました",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
                else:
                    return redirect("chco")
        else:
            return redirect("home")
    else:
        return redirect("login")
    
@app.route("/medi",methods=["GET","POST"])
def medi():
    if "perm" in session:
        if session["perm"]==3:
            if request.method=="GET":
                token=secrets.token_hex()
                session["medi_in"]=token
                res="<form method=POST action=medi>\n"
                res=res+"<input type=hidden name=medi_in value=\""+token+"\">"
                res=res+"<table border=1 align=center style=\"border-collapse: collapse\">\n"
                res=res+"\t<tr><td>内服薬</td><td><input type=text name=medi placeholder=分からない場合は不明と書いてください required></td></tr>"
                res=res+"\t<tr><td colspan=2 align=right><input type=submit value=送信></td></tr>\n"
                res=res+"</table>\n</form>"
                return render_template("medi.html", res=res,title="内服薬を一つ入力してください",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
            elif request.method=="POST":
                if session["medi_in"]==request.form["medi_in"]:
                    medi=request.form["medi"]
                    token=secrets.token_hex()
                    session["medi"]=token
                    res="<form method=POST action=medi-comp>\n<table border=1 align=center style=\"border-collapse: collapse\">\n"
                    res=res+"\t<tr><td>内服薬</td><td>"+html.escape(medi)+"</td></tr>"
                    res=res+"\t<tr><td colspan=2 align=right><input type=submit value=登録><a href=medi>登録画面に戻る</a></td></tr>\n"
                    res=res+"<input type=hidden name=medi value=\""+html.escape(medi)+"\">"
                    res=res+"<input type=hidden name=medi_token value=\""+token+"\">"
                    res=res+"</table>"
                    return render_template("medi.html", res=res,title="以下の内容で登録しますか？",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
                else:
                    return redirect("medi")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/medi-comp",methods=["GET","POST"])
def medi_comp():
    if "perm" in session:
        if session["perm"]==3:
            if request.method=="GET":
                return redirect("medi")
            elif request.method=="POST":
                if session["medi"]==request.form["medi_token"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    medi=request.form["medi"]
                    t=(session["user_id"],medi)
                    cur.execute("INSERT INTO med (pati_id,med) VALUES (?,?)",t)
                    conn.commit()
                    conn.close()
                    return render_template("medi.html", title="以下の内容で登録しました",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
                else:
                    return redirect("medi")
        else:
            return redirect("home")
    else:
        return redirect("login")

    
@app.route("/vital",methods=["GET","POST"])
def vital():
    if "perm" in session:
        if session["perm"]==3:
            if request.method=="GET":
                token=secrets.token_hex()
                session["vital"]=token
                res="<input type=hidden name=vital value=\""+token+"\">"
                return render_template("vital.html", res=res,title="体調報告画面",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
            elif request.method=="POST":
                if session["vital"]==request.form["vital"]:
                    token=secrets.token_hex()
                    session["vital-check"]=token
                    temp=request.form["temp"]
                    press_max=request.form["press_max"]
                    press_min=request.form["press_min"]
                    beat=request.form["beat"]
                    spo2=request.form["spo2"]
                    eat=request.form["eat"]
                    res="<form method=POST action=vital-comp>\n<table align=center>\n"
                    res=res+"\t<tr><td>体温</td><td>"+str(temp)+"</td></tr>"
                    res=res+"\t<tr><td>血圧（上）</td><td>"+str(press_max)+"</td></tr>"
                    res=res+"\t<tr><td>血圧（下）</td><td>"+str(press_min)+"</td></tr>"
                    res=res+"\t<tr><td>心拍数</td><td>"+str(beat)+"</td></tr>"
                    res=res+"\t<tr><td>血中酸素飽和度</td><td>"+str(spo2)+"</td></tr>"
                    res=res+"\t<tr><td>食事量</td><td>"+str(eat)+"</td></tr>"
                    res=res+"<input type=hidden name=temp value=\""+str(temp)+"\">\n"
                    res=res+"<input type=hidden name=press_max value=\""+str(press_max)+"\">\n"
                    res=res+"<input type=hidden name=press_min value=\""+str(press_min)+"\">\n"
                    res=res+"<input type=hidden name=beat value=\""+str(beat)+"\">\n"
                    res=res+"<input type=hidden name=spo2 value=\""+str(spo2)+"\">\n"
                    res=res+"<input type=hidden name=eat value=\""+str(eat)+"\">\n"
                    res=res+"<input type=hidden name=vital-check value=\""+token+"\">"
                    res=res+"\t<tr><td colspan=2 align=right><input type=submit value=送信><a href=vital>登録画面に戻る</a></td></tr>"
                    res=res+"</table>\n</form>"
                    return render_template("vital_comp.html", res=res,title="以下の内容で登録しますか？",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
                else:
                    return redirect("vital")
        else:
            return redirect("home")
    else:
        return redirect("login")
    
@app.route("/vital-comp",methods=["GET","POST"])
def vital_comp():
    if "perm" in session:
        if session["perm"]==3:
            if request.method=="GET":
                return redirect("vital")
            elif request.method=="POST":
                if session["vital-check"]==request.form["vital-check"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    temp=request.form["temp"]
                    press_max=request.form["press_max"]
                    press_min=request.form["press_min"]
                    beat=request.form["beat"]
                    spo2=request.form["spo2"]
                    eat=request.form["eat"]
                    res="<table align=center><tr><td><a href=home>ホームに戻る</a></td></tr></table>"
                    t=(session["user_id"],float(temp),int(press_max),int(press_min),int(spo2),int(eat),int(beat),str(datetime.datetime.today()))
                    cur.execute("INSERT INTO pati (pati_id,temp,press_max,press_min,spo2,eat,beat,time) VALUES (?,?,?,?,?,?,?,?)",t)
                    conn.commit()
                    conn.close()
                    return render_template("vital_comp.html", res=res,title="登録完了",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
                else:
                    return redirect("vital")
        else:
            return redirect("home")
    else:
        return redirect("login")


@app.route("/news",methods=["GET","POST"])
def news():
    if "perm" in session:
        if session["perm"]==3:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                res="<h2 align=center>医者からの連絡</h2>\n"
                cur.execute("SELECT title_id,title,doc_id FROM msgdoc WHERE pati_id=? ORDER BY time DESC",(int(session["user_id"]),))
                res=res+"<table align=center>\n"
                for col in cur:
                    cur2=conn.cursor()
                    cur2.execute("SELECT user_name FROM users WHERE user_id=?",(int(col[2]),))
                    for col2 in cur2:
                        res=res+"\t<tr><td>"+col2[0]+"</td><td><form method=POST action=news><input type=hidden name=title value="+str(col[0])+">"+col[1]+"</td><td><input type=submit value=閲覧></form></td></tr>\n"
                res=res+"</table>"
                conn.close()
                return render_template("news.html", res=res,title="連絡一覧",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                title_id=request.form["title"]
                cur.execute("SELECT title,msg FROM msgdoc WHERE title_id=?",(int(title_id),))
                res="<h2 align=center>医者からの連絡</h2>\n"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    res=res+"\t<tr><td>タイトル</td><td>"+col[0]+"</td></tr>\n"
                    res=res+"\t<tr><td colspan=2><pre>"+col[1]+"</pre></td></tr>"
                res=res+"</table>"
                res=res+"<h3 align=center><a href=news>連絡一覧に戻る</a></h3>"
                conn.close()
                return render_template("news.html", res=res,title="連絡事項",css=css,jquery=jquery,jsmart=jsmart,menu=menu_p)
        else:
            return redirect("home")
    else:
        return redirect("login")
    
@app.route("/vital-json")
def vital_json():
    dbname="test.db"
    conn=sql.connect(dbname,check_same_thread=False)
    cur=conn.cursor()
    user_id=request.args.get("id")
    out={}
    temp=[]
    prema=[]
    premi=[]
    spo2=[]
    beat=[]
    eat=[]
    time=[]
    cur.execute("SELECT temp,press_max,press_min,spo2,eat,beat,time FROM pati WHERE pati_id=?",(int(user_id),))
    for col in cur:
        temp.append(col[0])
        prema.append(col[1])
        premi.append(col[2])
        spo2.append(col[3])
        beat.append(col[4])
        eat.append(col[5])
        time.append(col[6][0:19])
    out["temp"]=temp
    out["prema"]=prema
    out["premi"]=premi
    out["spo2"]=spo2
    out["beat"]=beat
    out["eat"]=eat
    out["time"]=time
    conn.close()
    return jsonify(out)

#看護師・医者共通
@app.route("/patient",methods=["GET","POST"])
def patient():
    if "perm" in session:
        if session["perm"]==1 or session["perm"]==2:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                cur.execute("SELECT user_id,user_name FROM users WHERE perm=3")
                res="<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[1])+"</td><td><form method=POST action=patient><input name=id type=hidden value="+str(col[0])+"><input type=submit value=閲覧></form></td></tr>\n"
                res=res+"</table>"
                conn.close()
                if session["perm"]==1:
                    return render_template("paitent.html", res=res,title="患者一覧",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                elif session["perm"]==2:
                    return render_template("paitent.html", res=res,title="患者一覧",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                user_id=int(request.form["id"])
                cur.execute("SELECT user_name,birth,loca,tel,mail,room,num,tick FROM users WHERE user_id=?",(user_id,))
                for col in cur:
                    res="<h2 align=center>"+html.escape(col[0])+"さんの基本情報</h2>\n"
                    res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n"
                    res=res+"\t<tr><td>氏名</td><td>"+html.escape(col[0])+"</td><td>生年月日</td><td>"+html.escape(col[1])+"</td></tr>\n"
                    res=res+"\t<tr><td>住所</td><td colspan=3>"+html.escape(col[2])+"</td></tr>\n"
                    res=res+"\t<tr><td>電話番号</td><td colspan=3>"+html.escape(col[3])+"</td></tr>\n"
                    res=res+"\t<tr><td>メールアドレス</td><td colspan=3>"+html.escape(col[4])+"</td></tr>\n"
                    res=res+"<tr><td colspan=4><h3>入院情報</h3></td></tr>\n"
                    res=res+"\t<tr><td>病室</td><td colspan=2>保険証番号</td><td>診察券</td></tr>\n"
                    res=res+"\t<tr><td>"+html.escape(col[5])+"</td><td colspan=2>"+html.escape(col[6])+"</td><td>"+html.escape(col[7])+"</td></tr>\n"
                    cur2=conn.cursor()
                    cur2.execute("SELECT title,cont FROM chro WHERE pati_id=?",(user_id,))
                    res=res+"<tr><td colspan=4><h3>持病情報</h3></td></td>\n"
                    for col2 in cur2:
                        res=res+"\t<tr><td>持病名</td><td colspan=3>"+html.escape(col2[0])+"</td></tr>\n"
                        res=res+"\t<tr><td colspan=4><pre>"+html.escape(col2[1])+"</pre></td></tr>\n"
                    cur2.execute("SELECT med FROM med WHERE pati_id=?",(user_id,))
                    res=res+"<tr><td colspan=4><h3>内服薬情報</h3></td></tr>"
                    for col2 in cur2:
                        res=res+"\t<tr><td>薬品名</td><td colspan=3>"+html.escape(col2[0])+"</td></tr>"
                res=res+"</table>"
                conn.close()
                if session["perm"]==1:
                    return render_template("paitent2.html", user_id=user_id,res=res,title="入院者情報",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                elif session["perm"]==2:
                    return render_template("paitent2.html", user_id=user_id,res=res,title="入院者情報",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)  
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/result-add",methods=["GET","POST"])
def result_add():
    if "perm" in session:
        if session["perm"]==1 or session["perm"]==2:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                cur.execute("SELECT user_id,user_name FROM users WHERE perm=3")
                res="<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[1])+"</td><td><form method=POST action=result-add><input type=hidden name=user_id value="+str(col[0])+"><input type=submit value=編集></form></td></tr>\n"
                res=res+"</table>"
                conn.close()
                if session["perm"]==1:
                    return render_template("record_add_meibo.html", title="患者一覧",res=res,css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                elif session["perm"]==2:
                    return render_template("record_add_meibo.html", title="患者一覧",res=res,css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                token=secrets.token_hex()
                session["result-add"]=token
                user_id=int(request.form["user_id"])
                cur.execute("SELECT user_name,user_id FROM users WHERE user_id=?",(user_id,))
                tmp=[]
                for col in cur:
                    tmp.append(col[0])
                res="<table align=center><tr><td>"
                res=res+"<h3 align=center><a href=home>ホームに戻る</a></h3>\n"
                res=res+"</td><td><h3 align=center><a href=result-add>患者一覧</a></h3>"
                res=res+"</td></tr></table>"
                res=res+"<h2 align=center>過去の検査結果</td>\n"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n"
                cur.execute("SELECT user_id,time,result FROM test WHERE pati_id=? ORDER BY time DESC",(user_id,))
                for col in cur:
                    cur2=conn.cursor()
                    cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                    for col2 in cur2:
                        res=res+"\t<tr><td>担当者</td><td>"+html.escape(col2[0])+"</td><td>検査日時</td><td>"+col[1][0:19]+"</td></tr>\n"
                        res=res+"\t<tr><td colspan=4>検査結果<br><pre>"+html.escape(col[2])+"</pre></td></tr>\n"
                res=res+"</table>"
                conn.close()
                if session["perm"]==1:
                    return render_template("result_add.html", token=token,res=res,user_id=user_id,title=tmp[0],css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                elif session["perm"]==2:
                    return render_template("result_add.html", token=token,res=res,user_id=user_id,title=tmp[0],css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/result-add-check",methods=["GET","POST"])
def result_add_check():
    if "perm" in session:
        if session["perm"]==1 or session["perm"]==2:
            if request.method=="GET":
                return redirect("result-add")
            elif request.method=="POST":
                if session["result-add"]==request.form["result-add"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    token=secrets.token_hex()
                    session["result-add-check"]=token
                    cont=html.escape(request.form["cont"])
                    user_id=int(request.form["id"])
                    cur.execute("SELECT user_name FROM users WHERE user_id=?",(user_id,))
                    res="<form method=POST action=result-add-comp>\n<table align=center>"
                    res=res+"\t<input type=hidden name=user_id value="+str(user_id)+">"
                    res=res+"\t<input type=hidden name=cont value=\""+cont+"\">"
                    res=res+"\t<input type=hidden name=result-add-check value=\""+token+"\">"
                    for col in cur:
                        res=res+"\t<tr><td>患者名</td><td>"+html.escape(col[0])+"</td></tr>\n"
                    res=res+"\t<tr><td colspan=2>"+cont+"</td></tr>\n"
                    res=res+"\t<tr><td colspan=2><input type=submit value=確定></td></tr>\n"
                    res=res+"</table>\n</form>"
                    res=res+"<form method=POST action=result-add><table align=center>\n"
                    res=res+"<tr><td align=right><input type=hidden name=user_id value="+str(user_id)+"><input type=submit value=やり直す></td></tr>"
                    res=res+"</table>\n</form>"
                    conn.close()
                    if session["perm"]==1:
                        return render_template("result_add_check.html", res=res,title="こちらの内容で問題ありませんか?",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                    elif session["perm"]==2:
                        return render_template("result_add_check.html", res=res,title="こちらの内容で問題ありませんか?",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
                else:
                    return redirect("result-add")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/result-add-comp",methods=["GET","POST"])
def result_add_comp():
    if "perm" in session:
        if session["perm"]==1 or session["perm"]==2:
            if request.method=="GET":
                return redirect("result-add")
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                if session["result-add-check"]==request.form["result-add-check"]:
                    cont=request.form["cont"]
                    user_id=int(request.form["user_id"])
                    t=(session["user_id"],user_id,cont,str(datetime.datetime.today()))
                    cur.execute("INSERT INTO test (user_id,pati_id,result,time) VALUES (?,?,?,?)",t)
                    conn.commit()
                    conn.close()
                    if session["perm"]==1:
                        return render_template("result_add_comp.html", title="追加完了",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                    elif session["perm"]==2:
                        return render_template("result_add_comp.html", title="追加完了",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
                else:
                    return redirect("result-add")
        else:
            return redirect("home")
    else:
        return redirect("login")

#医者
@app.route("/ret",methods=["GET","POST"])
def ret():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                res="<table align=center border=1 style=\"border-collapse: collapse\">\n"
                cur.execute("SELECT user_name,user_id FROM users WHERE perm=3")
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[0])+"</td><td><form action=ret method=POST><input type=hidden name=user_id value="+str(col[1])+"><input type=submit value=記入></form></td></tr>"
                res=res+"</table>"
                conn.close()
                return render_template("calc_menu.html", res=res,title="患者様一覧",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                token=secrets.token_hex()
                session["ret"]=token
                user_id=request.form["user_id"]
                tmp=[]
                cur.execute("SELECT user_name FROM users WHERE user_id=?",(int(user_id),))
                for col in cur:
                    tmp.append(col[0])
                res="<table align=center>\n"
                res=res+"\t<tr><td align=center><h3><a href=home>ホームに戻る</a></h3></td>"
                res=res+"<td align=center><h3><a href=ret>患者一覧</a></h3></td></tr>\n"
                res=res+"</table>\n"
                cur.execute("SELECT doc_id,time,day,money FROM ret WHERE pati_id=? ORDER BY time DESC",(int(user_id),))
                res=res+"<h2 align=center>"+html.escape(tmp[0])+"様の退院情報</h2>\n"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    cur2=conn.cursor()
                    cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                    for col2 in cur2:
                        res=res+"\t<tr><td>記入医師</td><td>"+html.escape(col2[0])+"</td><td>記録日時</td><td>"+html.escape(col[1][0:19])+"</td></tr>\n"
                        res=res+"\t<tr><td>退院日</td><td>"+html.escape(str(col[2]))+"</td><td>医療費</td><td>"+str(col[3])+"円</td></tr>\n"
                res=res+"</table>\n</form>"
                conn.close()
                return render_template("calc.html", token=token,res=res,user_id=user_id,title=html.escape(tmp[0]),css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/ret-check",methods=["GET","POST"])
def ret_check():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                return redirect("ret")
            elif request.method=="POST":
                if session["ret"]==request.form["ret"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    token=secrets.token_hex()
                    session["ret-check"]=token
                    res="<input type=hidden name=ret-check value=\""+token+"\">"
                    user_id=request.form["user_id"]
                    money=request.form["money"]
                    day=html.escape(request.form["day"])
                    tmp=[]
                    cur.execute("SELECT user_name FROM users WHERE user_id=?",(int(user_id),))
                    for col in cur:
                        tmp.append(col[0])
                    conn.close()
                    return render_template("calc_check.html", res=res,user_id=user_id,user_name=html.escape(tmp[0]),money=str(money),day=str(day),money_form=str(money),user_id_form=str(user_id),day_form=str(day),title="以下の内容で登録しますか？",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    return redirect("ret")
        else:
            return redirect("home")
    else:
        return redirect("home")

@app.route("/ret-comp",methods=["GET","POST"])
def ret_comp():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                return redirect("ret")
            elif request.method=="POST":
                if session["ret-check"]==request.form["ret-check"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    user_id=int(request.form["user_id"])
                    money=int(request.form["money"])
                    day=str(request.form["day"])
                    t=(session["user_id"],user_id,day,money,str(datetime.datetime.today()))
                    cur.execute("INSERT INTO ret (doc_id,pati_id,day,money,time) VALUES (?,?,?,?,?)",t)
                    conn.commit()
                    conn.close()
                    return render_template("calc_comp.html", title="登録完了",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    return redirect("ret")
        else:
            return redirect("home")
    else:
        return redirect("home")
    
@app.route("/treat-add",methods=["GET","POST"])
def treat_add():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                cur.execute("SELECT user_id,user_name FROM users WHERE perm=3")
                res="<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[1])+"</td><td><form method=POST action=treat-add><input type=hidden name=user_id value="+str(col[0])+"><input type=submit value=編集></form></td></tr>\n"
                res=res+"</table>"
                conn.close()
                return render_template("treat_add_meibo.html", title="患者一覧",res=res,css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                token=secrets.token_hex()
                session["treat-add"]=token
                user_id=int(request.form["user_id"])
                cur.execute("SELECT user_name,user_id FROM users WHERE user_id=?",(user_id,))
                tmp=[]
                for col in cur:
                    tmp.append(col[0])
                res="<table align=center><tr><td>"
                res=res+"<h3 align=center><a href=home>ホームに戻る</a></h3>\n"
                res=res+"</td><td><h3 align=center><a href=treat-add>患者一覧</a></h3>"
                res=res+"</td></tr></table>"
                res=res+"<h2 align=center>治療に関する情報</h2>\n"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">"
                cur.execute("SELECT user_id,time,title,cont FROM act WHERE pati_id=? ORDER BY time DESC",(user_id,))
                for col in cur:
                    cur2=conn.cursor()
                    cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                    for col2 in cur2:
                        res=res+"\t<tr><td>担当者</td><td>"+html.escape(col2[0])+"</td><td>対応日時</td><td>"+col[1]+"</td></tr>\n"
                        res=res+"\t<tr><td>内容</td><td colspan=3>"+html.escape(col[2])+"</td></tr>\n"
                        res=res+"\t<tr><td colspan=4>方針<br><pre>"+html.escape(col[3])+"</pre></td></tr>\n"
                res=res+"</table>"
                conn.close()
                return render_template("treat_add.html", token=token,res=res,user_id=user_id,title=tmp[0],css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/treat-add-check",methods=["GET","POST"])
def treat_add_check():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                return redirect("treat-add")
            elif request.method=="POST":
                if session["treat-add"]==request.form["treat-add"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    token=secrets.token_hex()
                    session["treat-add-check"]=token
                    cont=html.escape(request.form["cont"])
                    title=html.escape(request.form["title"])
                    user_id=int(request.form["id"])
                    cur.execute("SELECT user_name FROM users WHERE user_id=?",(user_id,))
                    res="<form method=POST action=treat-add-comp>\n<table align=center>\n"
                    res=res+"\t<input type=hidden name=user_id value=\""+str(user_id)+"\">\n"
                    res=res+"\t<input type=hidden name=cont value=\""+cont+"\">\n"
                    res=res+"\t<input type=hidden name=title value=\""+title+"\">\n"
                    res=res+"\t<input type=hidden name=treat-add-check value=\""+token+"\">\n"
                    for col in cur:
                        res=res+"\t<tr><td>患者名</td><td>"+html.escape(col[0])+"</td></tr>\n"
                    res=res+"\t<tr><td>タイトル</td><td>"+title+"</td></tr>\n"
                    res=res+"\t<tr><td colspan=2>"+cont+"</td></tr>\n"
                    res=res+"\t<tr><td colspan=2><input type=submit value=確定></td></tr>\n"
                    res=res+"</table>\n</form>"
                    res=res+"<form method=POST action=treat-add><table align=center>\n"
                    res=res+"<tr><td align=right><input type=hidden name=user_id value="+str(user_id)+"><input type=submit value=やり直す></td></tr>"
                    res=res+"</table>\n</form>"
                    conn.close()
                    return render_template("treat_add_check.html", res=res,title="こちらの内容で問題ありませんか?",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    return redirect("treat-add")
        else:
            return redirect("home")
    else:
        return redirect("login")
    
@app.route("/treat-add-comp",methods=["GET","POST"])
def treat_add_comp():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                return redirect("treat-add")
            elif request.method=="POST":
                if session["treat-add-check"]==request.form["treat-add-check"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    cont=request.form["cont"]
                    title=request.form["title"]
                    user_id=int(request.form["user_id"])
                    t=(session["user_id"],user_id,title,cont,str(datetime.datetime.today()))
                    cur.execute("INSERT INTO act (user_id,pati_id,title,cont,time) VALUES (?,?,?,?,?)",t)
                    conn.commit()
                    conn.close()
                    return render_template("treat_add_comp.html", title="追加完了",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    return redirect("treat-add")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/record-add",methods=["GET","POST"])
def record_add():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                cur.execute("SELECT user_id,user_name FROM users WHERE perm=3")
                res="<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[1])+"</td><td><form method=POST action=record-add><input type=hidden name=id value="+str(col[0])+"><input type=submit value=編集></form></td></tr>\n"
                res=res+"</table>"
                conn.close()
                return render_template("record_add_meibo.html", title="患者一覧",res=res,css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                token=secrets.token_hex()
                session["record-add"]=token
                user_id=int(request.form["id"])
                cur.execute("SELECT user_name,user_id FROM users WHERE user_id=?",(user_id,))
                tmp=[]
                for col in cur:
                    tmp.append(col[0])
                res="<table align=center><tr><td>"
                res=res+"<h3 align=center><a href=home>ホームに戻る</a></h3>\n"
                res=res+"</td><td><h3 align=center><a href=record-add>患者一覧</a></h3>"
                res=res+"</td></tr></table>"
                res=res+"<h2 align=center>カルテ情報</h2>"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n"
                cur.execute("SELECT doc_id,time,cont FROM carte WHERE pati_id=? ORDER BY time DESC",(user_id,))
                for col in cur:
                    cur2=conn.cursor()
                    cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                    for col2 in cur2:
                        res=res+"\t<tr><td>記録者</td><td>"+html.escape(str(col2[0]))+"</td><td>記録日時</td><td>"+str(col[1])[0:19]+"</td></tr>\n"
                        res=res+"\t<tr><td colspan=4>"+html.escape(col[2])+"</td></tr>\n"
                res=res+"</table>"
                conn.close()
                return render_template("record_add.html", token=token,res=res,user_id=user_id,title=tmp[0],css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/record-add-check",methods=["GET","POST"])
def record_add_check():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                return redirect("record-add")
            elif request.method=="POST":
                if session["record-add"]==request.form["record-add"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    token=secrets.token_hex()
                    session["record-add-check"]=token
                    cont=html.escape(request.form["cont"])
                    user_id=int(request.form["id"])
                    cur.execute("SELECT user_name FROM users WHERE user_id=?",(user_id,))
                    res="<form method=POST action=record-add-comp>\n<table align=center>"
                    res=res+"\t<input type=hidden name=user_id value=\""+str(user_id)+"\">"
                    res=res+"\t<input type=hidden name=cont value=\""+cont+"\">"
                    res=res+"\t<input type=hidden name=record-add-check value=\""+token+"\">"
                    for col in cur:
                        res=res+"\t<tr><td>患者名</td><td>"+html.escape(col[0])+"</td></tr>"
                    res=res+"\t<tr><td colspan=2>"+cont+"</td></tr>"
                    res=res+"\t<tr><td colspan=2><input type=submit value=確定></td></tr>"
                    res=res+"</table>\n</form>"
                    res=res+"<form method=POST action=record-add><table align=center>\n"
                    res=res+"<tr><td align=right><input type=hidden name=id value=\""+str(user_id)+"\"><input type=submit value=やり直す></td></tr>"
                    res=res+"</table>\n</form>"
                    conn.close()
                    return render_template("record_add_check.html", res=res,title="こちらの内容で問題ありませんか?",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    return redirect("record-add")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/record-add-comp",methods=["GET","POST"])
def record_add_comp():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                return redirect("record-add")
            elif request.method=="POST":
                if session["record-add-check"]==request.form["record-add-check"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    cont=request.form["cont"]
                    user_id=int(request.form["user_id"])
                    t=(session["user_id"],user_id,cont,str(datetime.datetime.today()))
                    cur.execute("INSERT INTO carte (doc_id,pati_id,cont,time) VALUES (?,?,?,?)",t)
                    conn.commit()
                    conn.close()
                    return render_template("record_add_comp.html", title="追加完了",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    return redirect("record-add")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/register",methods=["GET","POST"])
def register():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                token=secrets.token_hex()
                session["register"]=token
                return render_template("register.html", token=token,title="利用者登録画面",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
            elif request.method=="POST":
                if session["register"]==request.form["register"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    cur.execute("SELECT user_id FROM users WHERE mail=?",(request.form["mail"],))
                    tmp=[]
                    for col in cur:
                        tmp.append(col)
                    if len(tmp)==0:
                        t=(request.form["user_name"],gph(request.form["pass"]),int(request.form.get("perm")),request.form["room"],request.form["num"],request.form["tick"],str(datetime.datetime.today()),request.form["loca"],request.form["tel"],request.form["mail"],request.form["birth"])
                        cur.execute("INSERT INTO users (user_name,pass,perm,room,num,tick,time,loca,tel,mail,birth) VALUES(?,?,?,?,?,?,?,?,?,?,?)",t)
                        conn.commit()
                        cate={}
                        cate["1"]="医者"
                        cate["2"]="看護師"
                        cate["3"]="患者"
                        res="<table align=center>\n\t"
                        res=res+"<tr><td>名前</td><td>"+html.escape(request.form["user_name"])+"</td></tr>\n\t"
                        res=res+"<tr><td>種別</td><td>"+html.escape(cate[request.form.get("perm")])+"</td></tr>\n\t"
                        res=res+"<tr><td>部屋(病室)</td><td>"+html.escape(request.form["room"])+"</td></tr>\n\t"
                        res=res+"<tr><td>保険証番号</td><td>"+html.escape(request.form["num"])+"</td></tr>\n\t"
                        res=res+"<tr><td>診察券</td><td>"+html.escape(request.form["tick"])+"</td></tr>\n\t"
                        res=res+"<tr><td>住所</td><td>"+html.escape(request.form["loca"])+"</td></tr>\n\t"
                        res=res+"<tr><td>携帯電話番号</td><td>"+html.escape(request.form["tel"])+"</td></tr>\n\t"
                        res=res+"<tr><td>メールアドレス</td><td>"+html.escape(request.form["mail"])+"</td></tr>\n\t"
                        res=res+"<tr><td>生年月日</td><td>"+html.escape(request.form["birth"])+"</td></tr>\n\t"
                        res=res+"<tr><td></td><td><a href=register>入力画面に戻る</a><br><a href=home>ホーム画面に戻る</a><br></td></tr>\n\t"
                        conn.close()
                        return render_template("register_comp.html", css=css,jquery=jquery,jsmart=jsmart,menu=menu_d,res=res)
                    else:
                        conn.close()
                        return render_template("register.html", title="アドレスが重複しています",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    redirect("register")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/msg-doc",methods=["GET","POST"])
def msg_doc():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                cur.execute("SELECT user_name,user_id FROM users WHERE perm=3")
                res="<table align=center border=1 style=\"border-collapse: collapse\">"
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[0])+"</td><td><form action=msg-doc method=POST><input type=hidden value="+str(col[1])+" name=user_id><input type=submit value=作成></form></td></tr>"
                conn.close()
                return render_template("msg_doc_menu.html",res=res,title="連絡先一覧",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                token=secrets.token_hex()
                session["msg-doc"]=token
                user_id=int(request.form["user_id"])
                tmp=[]
                cur.execute("SELECT user_name FROM users WHERE user_id=?",(user_id,))
                for col in cur:
                    tmp.append(html.escape(col[0]))
                res="<table align=center><tr><td>"
                res=res+"<h3 align=center><a href=home>ホームに戻る</a></h3>\n"
                res=res+"</td><td><h3 align=center><a href=msg-doc>患者一覧</a></h3>"
                res=res+"</td></tr></table>"
                res=res+"<h2 align=center>過去の連絡</h2>\n"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n"
                t=(session["user_id"],user_id)
                cur.execute("SELECT title,msg,time FROM msgdoc WHERE doc_id=? AND pati_id=? ORDER BY time DESC",t)
                for col in cur:
                    res=res+"\t<tr><td>タイトル</td><td>"+col[0]+"</td><td>連絡日時</td><td>"+col[2]+"</td></tr>"
                    res=res+"\t<tr><td colspan=4><pre>"+col[1]+"</pre></td></tr>"
                res=res+"</table>"
                conn.close()
                return render_template("msg_doc.html", token=token,title=tmp[0]+"様への連絡",res=res,css=css,jquery=jquery,jsmart=jsmart,menu=menu_d,hide=user_id)
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/msg-doc-check",methods=["GET","POST"])
def msg_doc_check():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                return redirect("msg-doc")
            elif request.method=="POST":
                if session["msg-doc"]==request.form["msg-doc"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    token=secrets.token_hex()
                    session["msg-doc-check"]=token
                    user_id=int(request.form["user_id"])
                    title=html.escape(request.form["title"])
                    cont=html.escape(request.form["cont"])
                    res="<form action=msg-doc-comp method=POST>\n<input type=hidden name=user_id value="+str(user_id)+">\n<table align=center>\n"
                    res=res+"<input type=hidden name=title value=\""+title+"\">\n<input type=hidden name=cont value=\""+cont+"\">"
                    res=res+"<input type=hidden name=msg-doc-check value=\""+token+"\">"
                    res=res+"\t<tr><td>タイトル</td><td>"+title+"</td></tr>\n"
                    res=res+"\t<tr><td colspan=2>"+cont+"</td>\n"
                    cur.execute("SELECT user_name FROM users WHERE user_id=?",(user_id,))
                    for col in cur:
                        res=res+"\t<tr><td>連絡先</td><td>"+html.escape(col[0])+"</td></tr>"
                    res=res+"\t<tr><td colspan=2 align=right><input type=submit value=送信></td></tr>"
                    res=res+"</table>\n</form>\n"
                    res=res+"<form method=POST action=msg-doc><table align=center>\n"
                    res=res+"<tr><td align=right><input type=hidden name=user_id value="+str(user_id)+"><input type=submit value=やり直す></td></tr>"
                    res=res+"</table>\n</form>"
                    conn.close()
                    return render_template("msg_doc_menu.html", title="以下の内容で送信しますか？",res=res,css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    return redirect("msg-doc")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/msg-doc-comp",methods=["GET","POST"])
def msg_doc_comp():
    if "perm" in session:
        if session["perm"]==1:
            if request.method=="GET":
                return redirect("msg-doc")
            elif request.method=="POST":
                if session["msg-doc-check"]==request.form["msg-doc-check"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    cont=html.escape(request.form["cont"])
                    title=html.escape(request.form["title"])
                    user_id=int(request.form["user_id"])
                    t=(session["user_id"],user_id,title,cont,str(datetime.datetime.today()))
                    cur.execute("INSERT INTO msgdoc (doc_id,pati_id,title,msg,time) VALUES (?,?,?,?,?)",t)
                    conn.commit()
                    conn.close()
                    return render_template("msg_doc_comp.html", title="追加完了",css=css,jquery=jquery,jsmart=jsmart,menu=menu_d)
                else:
                    return redirect("msg-doc")
        else:
            return redirect("home")
    else:
        return redirect("login")
#看護師
@app.route("/record-info",methods=["GET","POST"])
def record_info():
    if "perm" in session:
        if session["perm"]==2:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                cur.execute("SELECT user_id,user_name FROM users WHERE perm=3")
                res="<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[1])+"</td><td><form action=record-info method=POST><input type=hidden name=user_id value="+str(col[0])+"><input type=submit value=閲覧></form></td></tr>"
                res=res+"</table>"
                conn.close()
                return render_template("record_info.html", res=res,title="患者様一覧",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                user_id=request.form["user_id"]
                cur.execute("SELECT user_name FROM users WHERE user_id=?",(int(user_id),))
                tmp=[]
                for col in cur:
                    tmp.append(col[0])
                cur.execute("SELECT doc_id,time,cont FROM carte WHERE pati_id=? ORDER BY time DESC",(int(user_id),))
                res="<table align=center><tr><td>"
                res=res+"<h3 align=center><a href=home>ホームに戻る</a></h3>\n"
                res=res+"</td><td><h3 align=center><a href=record-info>患者一覧</a></h3>"
                res=res+"</td></tr></table>"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    cur2=conn.cursor()
                    cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                    for col2 in cur2:
                        res=res+"\t<tr><td>記録者</td><td>"+html.escape(col2[0])+"</td><td>記録日時</td><td>"+html.escape(col[1][0:19])+"</td></tr>"
                        res=res+"\t<tr><td colspan=4><pre>"+html.escape(col[2])+"</pre></td></tr>"
                res=res+"</table>"
                conn.close()
                return render_template("record_info.html", res=res,title=tmp[0]+"様のカルテ情報",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/treat-info",methods=["GET","POST"])
def treat_info():
    if "perm" in session:
        if session["perm"]==2:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                cur.execute("SELECT user_id,user_name FROM users WHERE perm=3")
                res="<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[1])+"</td><td><form action=treat-info method=POST><input type=hidden name=user_id value="+str(col[0])+"><input type=submit value=閲覧></form></td></tr>"
                res=res+"</table>"
                conn.close()
                return render_template("treat_info.html", res=res,title="患者様一覧",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                user_id=request.form["user_id"]
                cur.execute("SELECT user_name FROM users WHERE user_id=?",(int(user_id),))
                tmp=[]
                for col in cur:
                    tmp.append(col[0])
                cur.execute("SELECT user_id,time,cont,title FROM act WHERE pati_id=? ORDER BY time DESC",(int(user_id),))
                res="<table align=center><tr><td>"
                res=res+"<h3 align=center><a href=home>ホームに戻る</a></h3>\n"
                res=res+"</td><td><h3 align=center><a href=treat-info>患者一覧</a></h3>"
                res=res+"</td></tr></table>"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">\n"
                for col in cur:
                    cur2=conn.cursor()
                    cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                    for col2 in cur2:
                        res=res+"\t<tr><td>記録者</td><td>"+html.escape(col2[0])+"</td><td>記録日時</td><td>"+html.escape(col[1][0:19])+"</td></tr>"
                        res=res+"\t<tr><td>タイトル</td><td colspan=3>"+html.escape(col[3])+"</td></tr>"
                        res=res+"\t<tr><td colspan=4><pre>"+html.escape(col[2])+"</pre></td></tr>"
                res=res+"</table>"
                conn.close()
                return render_template("treat_info.html", res=res,title=html.escape(tmp[0])+"様の治療内容",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
        else:
            return redirect("home")
    else:
        return redirect("login")
            
@app.route("/call",methods=["GET","POST"])
def call():
    if "perm" in session:
        if session["perm"]==2:
            if request.method=="GET":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                cur.execute("SELECT user_name,user_id FROM users WHERE perm=3")
                res="<table align=center border=1 style=\"border-collapse: collapse\">"
                for col in cur:
                    res=res+"\t<tr><td>"+html.escape(col[0])+"</td><td><form method=POST action=call><input type=hidden name=user_id value="+html.escape(str(col[1]))+"><input type=submit value=記入></form></td></tr>"
                res=res+"</table>"
                conn.close()
                return render_template("call_menu.html", res=res,title="患者様一覧",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                token=secrets.token_hex()
                session["call"]=token
                user_id=int(request.form["user_id"])
                tmp=[]
                cur.execute("SELECT user_name FROM users WHERE user_id=?",(user_id,))
                for col in cur:
                    tmp.append(col[0])
                res="<table align=center><tr><td>"
                res=res+"<h3 align=center><a href=home>ホームに戻る</a></h3>\n"
                res=res+"</td><td><h3 align=center><a href=call>患者一覧</a></h3>"
                res=res+"</td></tr></table>"
                res=res+"<h2 align=center>過去のナースコール内容</h2>"
                res=res+"<table align=center border=1 style=\"border-collapse: collapse\">"
                cur.execute("SELECT nur_id,time,call_cont,act_cont FROM call WHERE pati_id=? ORDER BY time DESC",(user_id,))
                for col in cur:
                    cur2=conn.cursor()
                    cur2.execute("SELECT user_name FROM users WHERE user_id=?",(col[0],))
                    for col2 in cur2:
                        res=res+"\t<tr><td>担当看護師</td><td>"+html.escape(col2[0])+"</td><td>処置日時</td><td>"+html.escape(col[1][0:19])+"</td></tr>"
                        res=res+"\t<tr><td colspan=4>コール内容<br><pre>"+html.escape(col[2])+"</pre></td></tr>"
                        res=res+"\t<tr><td colspan=4>処置内容<br><pre>"+html.escape(col[3])+"</pre></td></tr>"
                res=res+"</table>"
                conn.close()
                return render_template("call.html", token=token,res=res,user_id=user_id,title=html.escape(tmp[0]),css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/call-check",methods=["GET","POST"])
def call_check():
    if "perm" in session:
        if session["perm"]==2:
            if request.method=="GET":
                return redirect("call")
            elif request.method=="POST":
                if session["call"]==request.form["call"]:
                    token=secrets.token_hex()
                    session["call-check"]=token
                    user_id=html.escape(request.form["user_id"])
                    call_cont=html.escape(request.form["call_cont"])
                    act_cont=html.escape(request.form["act_cont"])
                    res="<form action=call-comp method=POST><table align=center>\n"
                    res=res+"<input type=hidden name=call_cont value=\""+call_cont+"\">\n"
                    res=res+"<input type=hidden name=act_cont value=\""+act_cont+"\">\n"
                    res=res+"<input type=hidden name=user_id value="+str(user_id)+">\n"
                    res=res+"<input type=hidden name=call-check value=\""+token+"\">"
                    res=res+"\t<tr><td>コール内容</td><td><pre>"+call_cont+"</pre></td></tr>\n"
                    res=res+"\t<tr><td>処置内容</td><td><pre>"+act_cont+"</pre></td></tr>\n"
                    res=res+"\t<tr><td colspan=2 align=right><input type=submit value=送信></td></tr>\n"
                    res=res+"</table>\n</form>\n"
                    res=res+"<form method=POST action=call><table align=center>\n"
                    res=res+"<tr><td align=right><input type=hidden name=user_id value="+str(user_id)+"><input type=submit value=やり直す></td></tr>"
                    res=res+"</table>\n</form>"
                    return render_template("call_check.html", res=res,title="以下の内容で登録しますか？",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
                else:
                    return redirect("call")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/call-comp",methods=["GET","POST"])
def call_comp():
    if "perm" in session:
        if session["perm"]==2:
            if request.method=="GET":
                return redirect("call")
            elif request.method=="POST":
                dbname="test.db"
                conn=sql.connect(dbname,check_same_thread=False)
                cur=conn.cursor()
                if session["call-check"]==request.form["call-check"]:
                    pati_id=request.form["user_id"]
                    call_cont=request.form["call_cont"]
                    act_cont=request.form["act_cont"]
                    t=(session["user_id"],pati_id,call_cont,act_cont,str(datetime.datetime.today()))
                    cur.execute("INSERT INTO call (nur_id,pati_id,call_cont,act_cont,time) VALUES (?,?,?,?,?)",t)
                    conn.commit()
                    conn.close()
                    return render_template("call_comp.html", title="登録完了",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
                else:
                    return redirect("call")
        else:
            return redirect("home")
    else:
        return redirect("login")

@app.route("/msg-nur",methods=["GET","POST"])
def msg_nur():
    if "perm" in session:
        if session["perm"]==2:
            if request.method=="GET":
                token=secrets.token_hex()
                session["msg-nur"]=token
                return render_template("msg_nur.html", token=token,title="医師への連絡",css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
            elif request.method=="POST":
                if session["msg-nur"]==request.form["msg-nur"]:
                    token=secrets.token_hex()
                    session["msg-nur-check"]=token
                    title=html.escape(request.form["title"])
                    cont=html.escape(request.form["cont"])
                    res="<form action=msg-nur-comp method=POST><table align=center>"
                    res=res+"<input type=hidden name=title value=\""+title+"\">"
                    res=res+"<input type=hidden name=cont value=\""+cont+"\">"
                    res=res+"<input type=hidden name=msg-nur-check value=\""+token+"\">"
                    res=res+"\t<tr><td>タイトル</td><td>"+title+"</td></tr>"
                    res=res+"\t<tr><td>内容</td><td><pre>"+cont+"</pre></td></tr>"
                    res=res+"\t<tr><td colspan=2><input type=submit value=送信></td></tr>"
                    res=res+"</table>\n"
                    res=res+"<h3 align=center><a href=msg-nur>やり直す</a><h3>"
                    return render_template("msg_nur_comp.html", title="以下の内容で送信しますか？",res=res,css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
                else:
                    return redirect("msg-nur")
        else:
            return redirect("home")
    else:
        return redirect("login")
                
@app.route("/msg-nur-comp",methods=["GET","POST"])
def msg_nur_comp():
    if "perm" in session:
        if session["perm"]==2:
            if request.method=="GET":
                return redirect("msg-nur")
            elif request.method=="POST":
                if session["msg-nur-check"]==request.form["msg-nur-check"]:
                    dbname="test.db"
                    conn=sql.connect(dbname,check_same_thread=False)
                    cur=conn.cursor()
                    title=html.escape(request.form["title"])
                    cont=html.escape(request.form["cont"])
                    t=(session["user_id"],title,cont,str(datetime.datetime.today()))
                    cur.execute("INSERT INTO msgnur (nurse_id,title,msg,time) VALUES (?,?,?,?)",t)
                    conn.commit()
                    conn.close()
                    res="<h2 align=center><a href=home>ホームに戻る</a></h2>"
                    return render_template("msg_nur_comp.html", title="登録完了",res=res,css=css,jquery=jquery,jsmart=jsmart,menu=menu_n)
                else:
                    return redirect("msg-nur")
        else:
            return redirect("home")
    else:
        return redirect("login")

#ログアウト画面・セッションを無くす
@app.route("/logout")
def end():
    session.pop("user_id",None)
    res="<h3 align=center><a href=login>ログイン画面へ移動</a></h3>"
    return render_template("login.html", title="ログアウトしました",css=css,jquery=jquery,jsmart=jsmart,res=res)


#クリックインジェクション
@app.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0")#,ssl_context=('openssl/server.crt', 'openssl/server.key'))
