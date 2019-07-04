FROM python:3.7-stretch AS compile-image
WORKDIR /code
RUN apt-get update  &&\
  apt-get install --no-install-recommends -y build-essential gcc mysql-server cron pandoc r-base r-base-dev gdebi-core &&\
  wget https://download3.rstudio.org/ubuntu-14.04/x86_64/shiny-server-1.5.9.923-amd64.deb &&\
  gdebi -n shiny-server-1.5.9.923-amd64.deb && \
  rm /srv/shiny-server/index.html
RUN R -e "install.packages(c('shiny','rmarkdown','reticulate'),repos='https://cran.rstudio.com/')"
RUN pip install pandas matplotlib requests mysql-connector
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab && crontab /etc/cron.d/crontab && touch /var/log/cron.log
COPY reports /srv/shiny-server/reports/
COPY main.py r_template.py ./
COPY shiny-server.conf /etc/shiny-server/shiny-server.conf
COPY start .
CMD ["./start"] 
