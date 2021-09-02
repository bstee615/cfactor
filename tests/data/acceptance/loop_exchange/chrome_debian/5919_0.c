static void purple_gg_buddylist_export ( PurpleConnection * gc ) {
 struct im_connection * ic = purple_ic_by_gc ( gc ) ;
 if ( set_getstr ( & ic -> acc -> set , "gg_sync_contacts" ) ) {
 GList * actions = gc -> prpl -> info -> actions ( gc -> prpl , gc ) ;
 GList * p ;
 for ( p = g_list_first ( actions ) ;
 p ;
 p = p -> next ) {
 if ( ( ( PurplePluginAction * ) p -> data ) && purple_menu_cmp ( ( ( PurplePluginAction * ) p -> data ) -> label , "Upload buddylist to Server" ) == 0 ) {
 PurplePluginAction action ;
 action . plugin = gc -> prpl ;
 action . context = gc ;
 action . user_data = NULL ;
 ( ( PurplePluginAction * ) p -> data ) -> callback ( & action ) ;
 break ;
 }
 }
 g_list_free ( actions ) ;
 }
 }