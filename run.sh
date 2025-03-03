#!/bin/bash

folder_name="results"
e_commerce_server="e-commerce-server"
patio_api="patio-api"
petclinic_graphql="petclinic-graphql"
react_finland="react-finland"
timbuctoo="timbuctoo"

if [ ! -d "$folder_name" ]; then
    mkdir "$folder_name"
    if [ ! $? -eq 0 ]; then
        echo "Error: Failed to create folder '$folder_name'."
        exit 1
    fi
fi

for arg in "$@"; do
    if [[ $arg == $e_commerce_server ]]; then
        continue
    elif [[ $arg == $patio_api ]]; then
        continue
    elif [[ $arg == $petclinic_graphql ]]; then
        continue
    elif [[ $arg == $react_finland ]]; then
        continue
    elif [[ $arg == $timbuctoo ]]; then
        continue
    else
        echo "'$arg' wrong argument!"
        exit 1

    fi

done

docker build -t base_image ./base_image
docker run base_image --name base_image

for arg in "$@"; do
    if [[ $arg == $e_commerce_server ]]; then
        echo "running e-commerce-server..."
        if [ ! -d "$folder_name/$e_commerce_server" ]; then
            mkdir "$folder_name/$e_commerce_server"
            if [ ! $? -eq 0 ]; then
                echo "Error: Failed to create folder '$folder_name/$e_commerce_server'."
                exit 1
            fi
        fi
        docker build -t $e_commerce_server ./targets/$e_commerce_server
        docker run -d --name $e_commerce_server -p 5000:5000 $e_commerce_server
        RUNNING_CONTAINER_ID=$(docker ps -qf "name=$e_commerce_server")
        clairvoyance http://localhost:5000/graphql -o schema.json
        mv schema.json results/$e_commerce_server
        docker stop $(docker ps -q --filter "ancestor=$e_commerce_server")
        docker rm $(docker ps -a -q --filter "ancestor=$e_commerce_server")
        docker rmi $e_commerce_server
    elif [[ $arg == $patio_api ]]; then
        echo "running patio-api..."
        if [ ! -d "$folder_name/$patio_api" ]; then
            mkdir "$folder_name/$patio_api"
            if [ ! $? -eq 0 ]; then
                echo "Error: Failed to create folder '$folder_name/$patio_api'."
                exit 1
            fi
        fi
        docker build -t $patio_api ./targets/$patio_api
        CONTAINER_ID=(docker run -d --name $patio_api -p 5000:5000 $patio_api)
        sleep 40
        clairvoyance localhost:5000 -o schema.json
        mv schema.json results/$patio_api
        docker kill $CONTAINER_ID
        docker rm $CONTAINER_ID
        docker rmi $patio_api
    elif [[ $arg == $petclinic_graphql ]]; then
        echo "running petclinic-graphql..."
        if [ ! -d "$folder_name/$petclinic_graphql" ]; then
            mkdir "$folder_name/$petclinic_graphql"
            if [ ! $? -eq 0 ]; then
                echo "Error: Failed to create folder '$folder_name/$petclinic_graphql'."
                exit 1
            fi
        fi
        docker build -t $petclinic_graphql ./targets/$petclinic_graphql
        CONTAINER_ID=(docker run -d --name $petclinic_graphql -p 5000:9977 $petclinic_graphql)
        clairvoyance http://localhost:5000/graphql -o schema.json
        mv schema.json results/$petclinic_graphql
        docker kill $CONTAINER_ID
        docker rm $CONTAINER_ID
        docker rmi $patio_api

    elif [[ $arg == $react_finland ]]; then
        echo "running react-finland..."
        if [ ! -d "$folder_name/$react_finland" ]; then
            mkdir "$folder_name/$react_finland"
            if [ ! $? -eq 0 ]; then
                echo "Error: Failed to create folder '$folder_name/$react_finland'."
                exit 1
            fi
        fi
        docker build -t $react_finland ./targets/$react_finland
        CONTAINER_ID=$(docker run -d -p3000:3000 $react_finland)
        sleep 40
        clairvoyance http://localhost:3000/graphql -o schema.json
        pip install graphql-schema-diff
        pip install argparse
        python3 introspection_to_sql.py ./schema.json ./schema.graphql
        mv -t results/$react_finland ./schema.json ./schema.graphql
        schemadiff -o targets/$react_finland/schema.graphqls -n results/$react_finland/schema.graphql --as-json >./results/$react_finland/changes.json
        docker kill $CONTAINER_ID
        docker rm $(docker p s -aq --filter ancestor=$react_finland)
        docker rmi $react_finland

    else
        echo "running timbuctoo..."
        if [ ! -d "$folder_name/$timbuctoo" ]; then
            mkdir "$folder_name/$timbuctoo"
            if [ ! $? -eq 0 ]; then
                echo "Error: Failed to create folder '$folder_name/$timbuctoo'."
                exit 1
            fi
        fi
        docker build -t $timbuctoo ./targets/$timbuctoo
        docker run -d --name $timbuctoo -p 5000:80 $timbuctoo
        CONTAINER_ID=(docker run -p5000:80 huygensing/timbuctoo)
        docker run -d -p5000:80 huygensing/timbuctoo
        sleep 40
        echo $CONTAINER_ID
        clairvoyance http://localhost:5000/static/graphiq -o schema.json
        mv schema.json results/$timbuctoo

    fi

done

exit 0
