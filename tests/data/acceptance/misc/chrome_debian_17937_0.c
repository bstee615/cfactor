vpx_codec_err_t vpx_svc_encode ( SvcContext * svc_ctx , vpx_codec_ctx_t * codec_ctx , struct vpx_image * rawimg , vpx_codec_pts_t pts , int64_t duration , int deadline ) {
 vpx_codec_err_t res ;
 vpx_codec_iter_t iter ;
 const vpx_codec_cx_pkt_t * cx_pkt ;
 SvcInternal * const si = get_svc_internal ( svc_ctx ) ;
 if ( svc_ctx == NULL || codec_ctx == NULL || si == NULL ) {
 return VPX_CODEC_INVALID_PARAM ;
 }
 svc_log_reset ( svc_ctx ) ;
 res = vpx_codec_encode ( codec_ctx , rawimg , pts , ( uint32_t ) duration , 0 , deadline ) ;
 if ( res != VPX_CODEC_OK ) {
 return res ;
 }
 iter = NULL ;
 while ( ( cx_pkt = vpx_codec_get_cx_data ( codec_ctx , & iter ) ) ) {
 switch ( cx_pkt -> kind ) {
 # if CONFIG_SPATIAL_SVC case VPX_CODEC_SPATIAL_SVC_LAYER_PSNR : {
 int i ;
 for ( i = 0 ;
 i < svc_ctx -> spatial_layers ;
 ++ i ) {
 int j ;
 svc_log ( svc_ctx , SVC_LOG_DEBUG , "SVC frame: %d, layer: %d, PSNR(Total/Y/U/V): " "%2.3f %2.3f %2.3f %2.3f \n" , si -> psnr_pkt_received , i , cx_pkt -> data . layer_psnr [ i ] . psnr [ 0 ] , cx_pkt -> data . layer_psnr [ i ] . psnr [ 1 ] , cx_pkt -> data . layer_psnr [ i ] . psnr [ 2 ] , cx_pkt -> data . layer_psnr [ i ] . psnr [ 3 ] ) ;
 svc_log ( svc_ctx , SVC_LOG_DEBUG , "SVC frame: %d, layer: %d, SSE(Total/Y/U/V): " "%2.3f %2.3f %2.3f %2.3f \n" , si -> psnr_pkt_received , i , cx_pkt -> data . layer_psnr [ i ] . sse [ 0 ] , cx_pkt -> data . layer_psnr [ i ] . sse [ 1 ] , cx_pkt -> data . layer_psnr [ i ] . sse [ 2 ] , cx_pkt -> data . layer_psnr [ i ] . sse [ 3 ] ) ;
 for ( j = 0 ;
 j < COMPONENTS ;
 ++ j ) {
 si -> psnr_sum [ i ] [ j ] += cx_pkt -> data . layer_psnr [ i ] . psnr [ j ] ;
 si -> sse_sum [ i ] [ j ] += cx_pkt -> data . layer_psnr [ i ] . sse [ j ] ;
 }
 }
 ++ si -> psnr_pkt_received ;
 break ;
 }
 case VPX_CODEC_SPATIAL_SVC_LAYER_SIZES : {
 int i ;
 for ( i = 0 ;
 i < svc_ctx -> spatial_layers ;
 ++ i ) si -> bytes_sum [ i ] += cx_pkt -> data . layer_sizes [ i ] ;
 break ;
 }
 # endif default : {
 break ;
 }
 }
 }
 return VPX_CODEC_OK ;
 }