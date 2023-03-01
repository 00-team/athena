
SPACER="======================================"
EG="🔷"

cd /bots/athena/
source .env/bin/activate

OLD_COMMIT=$(git rev-parse HEAD)

echo "$EG update the source"
git pull
echo $SPACER

NEW_COMMIT=$(git rev-parse HEAD)

function check_diff {
    local file_has_changed=$(git diff --name-only $OLD_COMMIT...$NEW_COMMIT --exit-code $1)
    if [ -z "$file_has_changed" ]; then
        return 1
    else
        return 0
    fi
}

if check_diff "requirements.txt"; then
    echo "$EG install pip packages"
    pip install -r requirements.txt
    echo $SPACER
fi

if check_diff "athena.service"; then
    echo "$EG update uwsgi service"
    cp athena.service /etc/systemd/system/ --force
    systemctl daemon-reload
    echo $SPACER
fi

echo "$EG restart athena service"
systemctl restart athena
echo $SPACER

echo "Deploy is Done! ✅"

