import smtplib


def mail(pro_name,r,e):
    fromaddr = "cse.pspatel@gmail.com"
    password = "Pratik7598"
    #toaddr = []
    #toaddr += "pratikpatel0798@gmail.com"
    #toaddr += "dhruvsaraiya5144@gmail.com"
    #toaddr += "pranayshah93@gmail.com"
    toaddr = "pratikpatel0798@gmail.com"
    message = "Subject : {}\n".format("Crawling Job")
    message += "Content-type:text/html"
    temp = ""
    if e == "":
        temp += "\nCrawling for <strong>" + pro_name + "</strong> with Request Id = " + str(r) + " is done, check that out!!"
    else:
        temp += "\nThere is Error of " + e + " \nin Crawling for  " + pro_name + " with Request Id = " + str(r)

    message += "\n" + temp
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(fromaddr, password)
        server.sendmail(fromaddr, toaddr, message)
        server.quit()
        print("Mail Sent : ", message)
    except Exception as err:
        print("Exception : ", message,str(err))

