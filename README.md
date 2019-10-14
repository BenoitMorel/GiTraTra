# GiTraTra
Github Traffic Tracker: track your traffic on GitHub!

# What for?

Github provides a [page](https://help.github.com/en/articles/viewing-traffic-to-a-repository) to monitor how many times your project was viewed or cloned. But this page only records views and clones from the last 14 days.
GiTraTra is a python script that keeps track of your traffic over the time.

# How does it work?

GiTraTra must be ran at least once every 14 days. It queries github servers through its web API and stores the traffic statistics into a local file.

# Requirements

* Python
* The PyGithub python package: `pip install --user PyGithub`

# Running GiTraTra

The scripts takes the following parameters:
* An [authentification token](https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line), with at least `public_repo` enabled, or your username and password. Do NOT share the token, as it grants write access to your repositories! This level of authentification is unfortunately required to query repository traffic.
* A file containing the list of repository names (one per line, see examples).
* An output file path. GiTraTra reads and writes your traffic in this output file. I advise you to store backups of this file, or to version it with git. 

```
python gitratra.py token:<your_token> <repository_file> <output_file>
```
or
```
python gitratra.py username:<your_username> <repository_file> <output_file>
```
In the second case, you will be asked to prompt your password.

You are responsible for running the script at least once every 14 days and to make sure you don't lose the output_file (use backups or git!).

# Security

As written previously, the authentification token grants write access on your repository. 
GiTraTra only uses the token or your username+password for querying the traffic on your repositories, and does not store them anywhere. The results of the query are saved on your local machine only.

You are responsible for not sharing your token or password with any other person.


# Disclaimer on the concept of "unique" cloners and viewers

I am not sure how GitHub defines "unique". But you have to be aware that GiTraTra stores unique cloners and viewers per day, which means that if a "unique cloner" clones your repository once per day, it will be counted once per day. The number of unique cloners is NOT the number of different users.





