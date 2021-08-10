find abm ctestsuite zitser toyota -type d -name src > src.txt
for s in $(cat src.txt); do pushd $(dirname $s); mv src/* .; rm -r src; popd; done