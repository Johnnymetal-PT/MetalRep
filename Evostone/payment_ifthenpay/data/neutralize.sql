-- disable ifthenpay payment provider
UPDATE payment_provider
   SET ifthenpay_entity = NULL,
       ifthenpay_subentity = NULL,
       ifthenpay_backoffice_key = NULL,
       ifthenpay_antiphishing_key = NULL,
       ifthenpay_mbway_key = NULL,
       ifthenpay_mbway_description = NULL;
