-- disable eupago payment provider
UPDATE payment_provider
   SET eupago_api_key = NULL,
       eupago_client_id = NULL,
       eupago_client_secret = NULL;
