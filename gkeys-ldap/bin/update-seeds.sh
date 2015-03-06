#!/bin/sh
# $Id: update-seeds.sh,v 0.2.1 2014/10/12 dolsen Exp $

# configuration to run from a checkout with a custom config
cwd=$(pwd)
source ${cwd}/update-seeds.conf
source ${cwd}/testpath

die(){ echo "$@" 1>&2; exit 1; }
success(){ echo "$@"; exit 0; }

clone_api(){
    local target=dirname ${API_DIR}
    cd target
    git clone ${API_URL}
}

clone_gkey_seeds(){
    local target=dirname ${GKEY_SEEDS_DIR}
    cd target
    git clone ${GKEY_SEEDS_URL}
}

# start update process
echo "Beginning seed file update"

echo " *** updating gkey-seeds repo"
# update api checkout
if [[ ! -d ${GKEY_SEEDS_DIR} ]]; then
    clone_gkey_seeds
else
    cd ${GKEY_SEEDS_DIR} && git pull
fi

echo " *** updating api.gentoo.org repo"
# update api checkout
if [[ ! -d ${API_DIR} ]]; then
    clone_api
else
    cd ${API_DIR} && git pull
fi

echo " *** Fetching new seeds from LDAP"
cd ${GKEYS_DIR}
gkeys-ldap update-seeds -C gentoo-devs || die "Seed file generation failed... aborting"

echo " *** Checking if seed files are up-to-date"
if ! diff -q ${GKEYS_DIR}/${GKEYS_SEEDS} ${GKEY_SEEDS_DIR}/${GKEY_SEEDS} > /dev/null ;then
    echo " *** Spotted differences"
    echo " *** Updating old seeds with a new one"
    # copy seeds to gkey-seeds
    echo "  ... cp ${GKEYS_SEEDS} ${API_DIR}/${API_SEEDS}"
    cp ${GKEYS_SEEDS} ${GKEY_SEEDS_DIR}/${GKEY_SEEDS}
else
    success " *** No changes detected"
    exit 0
fi

echo "Signing new developers.seeds file"
gkeys sign -n ${GKEYS_SIGN} -F ${GKEY_SEEDS_DIR}/${GKEY_SEEDS} || die " *** Signing failed... exiting"

echo "Committing changes to gkey-seeds repo..."
cd ${GKEY_SEEDS_DIR}
git add ${GKEY_SEEDS}  || die " *** Failed to add modified ${GKEYS_SEEDS} file"
git add ${GKEY_SEEDS}.${GKEYS_SIG} || die " *** Failed to add ${GKEYS_SEEDS}.sig file"
git commit -m "${GKEYS_COMMIT_MSG}" || die " *** Failed to commit updates"
git push origin master || die " *** git push failed"
cd ..

echo "Committing changes to api repo..."
cp ${GKEY_SEEDS_DIR}/${GKEY_SEEDS} ${API_DIR}/${API_SEEDS} || die " *** Failed to copy modified ${GKEYS_SEEDS} file"
cp ${GKEY_SEEDS_DIR}/${GKEY_SEEDS}.${GKEYS_SIG} ${API_DIR}/${API_SEEDS}.${GKEYS_SIG} || die " *** Failed to copy modified ${GKEYS_SEEDS}.${GKEYS_SIG} file"
cd ${API_DIR}
git add ${API_SEEDS}  || die " *** Failed to add modified ${GKEYS_SEEDS} file"
git add ${API_SEEDS}.${GKEYS_SIG} || die " *** Failed to add ${GKEYS_SEEDS}.sig file"
git commit -m "${GKEYS_COMMIT_MSG}" || die " *** Failed to commit updates"
git push origin master || die " *** git push failed"

echo "Pushing the log file to ${LOG_UPLOAD_URL}"
LOG_FILE=$( cat "${LOG_DIR}/gkeys-ldap-lastlog" )
scp "${LOG_DIR}/${LOG_FILE}" "${LOG_UPLOAD_URL}"  || die "Failed to upload logfile: ${LOG_FILE}"

success "Successfully updated developer.seeds"

