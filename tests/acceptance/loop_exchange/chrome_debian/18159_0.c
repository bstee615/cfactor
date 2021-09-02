static int32_t strcmpAfterPrefix ( const char * s1 , const char * s2 , int32_t * pPrefixLength ) {
 int32_t pl = * pPrefixLength ;
 int32_t cmp = 0 ;
 s1 += pl ;
 s2 += pl ;
 for ( ;
 ;
 ) {
 int32_t c1 = ( uint8_t ) * s1 ++ ;
 int32_t c2 = ( uint8_t ) * s2 ++ ;
 cmp = c1 - c2 ;
 if ( cmp != 0 || c1 == 0 ) {
 break ;
 }
 ++ pl ;
 }
 * pPrefixLength = pl ;
 return cmp ;
 }