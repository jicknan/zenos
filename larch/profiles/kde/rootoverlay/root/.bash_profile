if [ -z "$DISPLAY" ] && [ -n "`echo $(tty) | grep /vc/1`" ]; then
    startx
fi
