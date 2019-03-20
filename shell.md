```
ls | xargs -n1 -I% bash -c "echo %"
```

range in bash

```
(for i in {0..199}; do echo $i; done) | xargs -n1 -I% bash -c 'echo $((%*10)):$((%*10+10))'
```

Read symlink value:
```
readlink -f /root/Public/myothertextfile.txt
```

update symlink value:
```
ln -sf /usr/local/cuda-9.0 /usr/local/cuda
```

find all files created +/- 1 day:
```
find . -maxdepth 1 -mtime -1
```

show file names + content:
```
more * | cat
```

```
find . -maxdepth 1 -mtime -0.3 | sort |  xargs -n1 -I% bash -c 'more %'
```

GPU:
```
 ps -ef|grep username
 sudo nvidia-smi -pl 150
 sudo service lightdm stop
 ```
 
 Firefox:

Run command into tmux:
```
tmux new-session -d -s "myTempSession" /opt/my_script.sh
```

