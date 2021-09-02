static void setup_environment ( int argc , char * * argv , int * argc_out , char * * * argv_out , char * * * argv_free , char * * env_free ) {
 int n , i , i0 ;
 char * p , * v = getenv ( "XDELTA" ) ;
 if ( v == NULL ) {
 ( * argc_out ) = argc ;
 ( * argv_out ) = argv ;
 ( * argv_free ) = NULL ;
 ( * env_free ) = NULL ;
 return ;
 }
 ( * env_free ) = ( char * ) main_malloc ( ( usize_t ) strlen ( v ) + 1 ) ;
 strcpy ( * env_free , v ) ;
 n = argc + 1 ;
 for ( p = * env_free ;
 * p != 0 ;
 ) {
 if ( * p ++ == ' ' ) {
 n ++ ;
 }
 }
 ( * argv_free ) = ( char * * ) main_malloc ( sizeof ( char * ) * ( n + 1 ) ) ;
 ( * argv_out ) = ( * argv_free ) ;
 ( * argv_out ) [ 0 ] = argv [ 0 ] ;
 ( * argv_out ) [ n ] = NULL ;
 i = 1 ;
 for ( p = * env_free ;
 * p != 0 ;
 ) {
 ( * argv_out ) [ i ++ ] = p ;
 while ( * p != ' ' && * p != 0 ) {
 p ++ ;
 }
 while ( * p == ' ' ) {
 * p ++ = 0 ;
 }
 }
 for ( i0 = 1 ;
 i0 < argc ;
 i0 ++ ) {
 ( * argv_out ) [ i ++ ] = argv [ i0 ] ;
 }
 ( * argc_out ) = i ;
 while ( i <= n ) {
 ( * argv_out ) [ i ++ ] = NULL ;
 }
 }