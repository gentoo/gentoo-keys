#!/bin/sh
# $Id: update-seeds.sh,v 0.2.1 2014/10/12 dolsen Exp $

# configuration to run from a checkout with a custom config
cwd=$(pwd)
source ${cwd}/update-seeds.conf
source ${cwd}/testpath

die(){ echo "$@" 1>&2; echo ""; exit 1; }
success(){ echo "$@"; echo ""; exit 0; }

clone_api(){
    local target=dirname ${API_DIR}
    cd target
    git clone ${API_URL}
}

# start update process
echo "Beginning seed file update"

echo " *** updating api.gentoo.org repo"
# update api checkout
if [[ ! -d ${API_DIR} ]]; then
    clone_api
else
    cd ${API_DIR} && git pull
fi

echo " *** Fetching new seeds from LDAP"
cd ${GKEYS_DIR}
gkeys-ldap -c ${GKEYS_CONF} updateseeds -C gentoo-devs || die "Seed file generation failed... aborting"

echo " *** Checking if seed files are up-to-date"
if ! diff -q ${GKEYS_DIR}/${GKEYS_SEEDS} ${API_DIR}/${API_SEEDS} > /dev/null ;then
    echo " *** Spotted differences"
    echo " *** Updating old seeds with a new one"
    # copy seeds to api
    echo "  ... cp ${GKEYS_SEEDS} ${API_DIR}/${API_SEEDS}"
    cp ${GKEYS_SEEDS} ${API_DIR}/${API_SEEDS}
else
    success " *** No changes detected"
fi

echo "Signing new developers.seeds file"
gkeys -c ${GKEYS_CONF} sign -n ${GKEYS_SIGN} -F ${API_DIR}/${API_SEEDS} || die " *** Signing failed... exiting"

echo "Committing changes to api repo..."
cd ${API_DIR}
git add ${API_SEEDS}  || die " *** Failed to add modified ${GKEYS_SEEDS} file"
git add ${API_SEEDS}.${GKEYS_SIG} || die " *** Failed to add ${GKEYS_SEEDS}.sig file"
git commit -m "${GKEYS_COMMIT_MSG}" || die " *** Failed to commit updates"
git push origin master || die " *** git push failed"

success "Successfully updated developer.seeds"

