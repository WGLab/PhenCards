docker ps | grep "phencards:test" | cut -d " " -f 1 | xargs docker kill
docker build -t phencards:test .
docker system prune -f
bash runsite.sh
