from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from sumit import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
from .tokens import generate_token


# Create your views here.
def home(request):
    return render(request, "authentication/index.html")


def signup(request):
    if request.method == "POST":

        # gaining form data
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        # first checking for already present username
        if User.objects.filter(username=username):
            messages.error(request, "redundant username")
            return redirect('home')

        # now checking redundant emails from database
        if User.objects.filter(email=email).exists():
            messages.error(request, "email already active!!")
            return redirect('home')

        # optional length check
        # if len(username) > 20:
        #     messages.error(request, "too long!!")
        #     return redirect('home')


        # confirm  password gone wrong
        if pass1 != pass2:
            messages.error(request, "confirm passwords not same!")
            return redirect('home')

        # optional check for alpha numeric username
        # if not username.isalnum():
        #     messages.error(request, "Username must be Alpha-Numeric!!")
        #     return redirect('home')

        # created a new user
        myuser = User.objects.create_user(username, email, pass1)

        # mentioning its properties
        myuser.first_name = fname
        myuser.last_name = lname


        # initially this user will not be active
        myuser.is_active = False

        # saving into database
        myuser.save()

        messages.success(request, "Check email for verifying")

        # email info goes here
        subject = "Login related"
        message = "account creation successful" + myuser.first_name + "! \n" + "\n. check for a verification mail. \n\n"
        from_email = settings.EMAIL_HOST_USER

        # recepient mail
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        # Email Address Confirmation Email
        current_site = get_current_site(request)
        email_subject = "this is confirmatory mail!"
        message2 = render_to_string('email_confirmation.html', {

            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })

        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )

        email.fail_silently = True
        email.send()

        return redirect('signin')

    return render(request, "authentication/signup.html")


# this will activate a user if EMAIL VERIFICATION IS DONE SUCCESSFULLY
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    # if user is found and token matching
    if myuser is not None and generate_token.check_token(myuser, token):

        # command for activating the user
        myuser.is_active = True

        # saving in database
        myuser.save()
        login(request, myuser)
        messages.success(request, "ACCOUNT ACTIVATION SUCCESSFUL!")
        return redirect('signin')
    else:
        # email verification faied
        return render(request, 'activation_failed.html')


def signin(request):
    if request.method == 'POST':

        # getting form data
        username = request.POST['username']
        pass1 = request.POST['pass1']

        # if not successful user will have None
        user = authenticate(username=username, password=pass1)

        # if login successful
        if user is not None:
            login(request, user)
            fname = user.first_name
            return render(request, "authentication/index.html", {"fname": fname})

        # else login failed
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect('home')

    return render(request, "authentication/signin.html")


# view for signout
def signout(request):
    # merely logout command in django
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')
