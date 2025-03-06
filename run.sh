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
        docker compose up --build
        # docker build -t $patio_api ./targets/$patio_api
        # docker run -d --name $patio_api -p 5000:5000 $patio_api
        # clairvoyance localhost:5000 -o schema.json
        # mv schema.json results/$patio_api

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
        docker run -d --name $petclinic_graphql -p 5000:5000 $petclinic_graphql
        clairvoyance http://localhost:3000/graphql -o schema.json
        mv schema.json results/$petclinic_graphql

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
        docker run -d --name $react_finland -p 5000:5000 $react_finland
        RUNNING_CONTAINER_ID=$(docker ps -qf "name=$react_finland")
        clairvoyance http://localhost:3000/graphql -o schema.json
        mv schema.json results/$react_finland
        docker stop $(docker ps -q --filter "ancestor=$react_finland")
        docker rm $(docker ps -a -q --filter "ancestor=$react_finland")
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
        docker run -d --name $timbuctoo -p 5000:5000 $timbuctoo
        clairvoyance localhost:5000 -o schema.json
        mv schema.json results/$timbuctoo

    fi

done

exit 0
