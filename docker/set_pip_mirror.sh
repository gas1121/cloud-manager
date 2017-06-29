if [ $USE_MIRROR ]; then
    if [ ! -f ~/.pip ]; then
        mkdir ~/.pip;
    fi
    mv /tmp/pip.conf ~/.pip/;
else
    rm /tmp/pip.conf;
fi