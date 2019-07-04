# Luuna Daily Salary Report App

## Setup 
You will need Docker and Docker Compose installed.
In order to run the infrastructure necessary to solve this challenge, simply clone or fork and clone this repository, cd into it's folder and execute the following command: 

```bash
docker-compose up 
```

Building will take a bit. ~30 mins on my somewhat decent connection.
 
This will build the database, server and web app.

If everything went well you should check

```
http://localhost:3838
```
Here you'll find a directory for shiny apps. You should check the folder `reports`. While the container is running this will be the folder where new reports will be.

Reports are named after the date, so just click any date and the app should be launched.

I've made two sample reports for demo.

## Libs used

* Pandas
* Matplotlib
* Shiny
* RMarkdown


I'm not a big fan of R, actually. It's seems to rely heavily on its IDE and I'm more of CLI guy. Up to this point I've never used Shiny or RMarkdown. I'll be using quite often from now on. Loved how easily apps can be made. Also, the `reticulate` package in R is fantastic.

## Development

Ok, you should look at the Dockerfile to get a feel of how things work.

In short, I use a python image with debian stretch as an OS. Then dependencies are installed. Here's the list:

* build-essential
* gcc 
* mysql-server
* cron 
* pandoc 
* r-base
* r-base-dev
* gdebi-core
* [Shiny server](https://www.rstudio.com/products/shiny/download-server/)
* requests
* mysql-connector

Just about everything we need.
This container will run two jobs. Running the Shiny server and schedule the `main.py` script to run daily noon using `cron`.

This script will connect to the `luunadb` database, and sample the `localhost:3000/speed` endpoint making a request every 5 seconds during 5 minutes.
Then it will fetch from the database each employee's information. 

Using pandas for data manipulation, the daily salary is calculated per employee.

And finally, the data sampled is saved to a csv file, and using a template a shiny app is generated per file. Shiny apps are served at `/srv/shiny-server/`

Each Shiny app is composed of `.rmd` file, this means that each app is static.
The server automatically finds this file and serves it as and html_document. Dead simple.

If at any time you wish to run the script manually, here's an easy way.

```
docker-compose exec web python main.py
```

## TODO

There are some improvements to be made. 

### Better front-end

Figuring out R and Shiny took me a long time. Thankfully the server shows a directory front by default. This could be a lot nicer.

### More useful analysis

Data visualization is not my strong suit. I tried to keep it simple and just show the information I was asked, so no fancy plots are used, but along with a better statistician than me, we could get some more useful data and plots.


