aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin {AWSID}.dkr.ecr.ap-southeast-1.amazonaws.com
docker image ls
docker tag linkdincrawler {AWSID}.dkr.ecr.ap-southeast-1.amazonaws.com/linkedincrawler:latest
docker push {AWSID}.dkr.ecr.ap-southeast-1.amazonaws.com/linkedincrawler:latest