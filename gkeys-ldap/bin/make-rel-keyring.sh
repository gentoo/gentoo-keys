#! /bin/sh

die(){ echo "$@" 1>&2; exit 1; }
success(){ echo "$@"; exit 0; }

timestamp=$(date +"%Y%m%d%H%M")
echo "timestamp = ${timestamp}"

filename="gentoo-keys-${timestamp}.tar.xz"
echo "filename = ${filename}"

target="/var/lib/gkeys/keyring-releases"
base="/var/lib/gkeys/keyrings"
src="gentoo"
repo="/var/lib/gkeys/gkey-seeds"
scptarget="dolsen@dev.gentoo.org:~/public_html/releases/keyrings/"

#cd /var/lib/gkeys || echo "failed to cd..." && exit 1

echo "Beginning tar..."
tar -cpJf $target/$filename --exclude-backups -C $base $src  || die "tar failed"

gkeys sign -F $target/$filename || die "Signing file failed"

# cd into gkey-seeds, create a tag

echo "Tagging gkey-seeds repo with release timestamp"

cd $repo
git tag -m "version bump: ${filename}" "${timestamp}"  || die "git tag creation failed"
git push --tags  || echo "Failed to push tags"

echo "${filename} created and signed..."
echo "Uploading to ${scptarget}..."
scp "${target}/${filename} ${scptarget}" || die "scp failed"
scp "${target}/${filename}.sig ${scptarget}" || die "scp failed"

success "Ready to bump ebuild"
