FROM base_image

RUN apt update && apt install curl git wget -y
RUN apt install default-jre -y
RUN apt install default-jdk -y
RUN wget https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz
RUN tar -xvf apache-maven-3.9.9-bin.tar.gz
RUN mv ./apache-maven-3.9.9 /opt/
RUN git clone https://github.com/HuygensING/timbuctoo.git
WORKDIR /timbuctoo
ENV M2_HOME='/opt/apache-maven-3.9.9'
ENV PATH="$M2_HOME/bin:$PATH"
RUN export PATH
RUN mvn clean package
CMD ["./timbuctoo_only.sh"]
