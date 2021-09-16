static void init_dequant_tables ( H264Context * h ) {
 int i , x ;
 init_dequant4_coeff_table ( h ) ;
 if ( h -> pps . transform_8x8_mode ) init_dequant8_coeff_table ( h ) ;
 if ( h -> sps . transform_bypass ) {
 for ( i = 0 ;
 i < 6 ;
 i ++ ) for ( x = 0 ;
 x < 16 ;
 x ++ ) h -> dequant4_coeff [ i ] [ 0 ] [ x ] = 1 << 6 ;
 if ( h -> pps . transform_8x8_mode ) for ( i = 0 ;
 i < 6 ;
 i ++ ) for ( x = 0 ;
 x < 64 ;
 x ++ ) h -> dequant8_coeff [ i ] [ 0 ] [ x ] = 1 << 6 ;
 }
 }