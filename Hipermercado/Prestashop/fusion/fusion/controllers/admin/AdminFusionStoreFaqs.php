<?php

use FusionStoreBundle\Entity\StoreFaqs as StoreFaqs;

class AdminFusionStoreFaqsController extends ModuleAdminController
{
  	public $bootstrap = true;

  	public function __construct()
  	{
        $this->className = '\FusionStoreBundle\Entity\StoreFaqs';
        $this->table = 'faqs';
        $this->identifier = 'id_faq';
        $this->lang = true;
        $this->add = true;
        $this->allow_export = false;

        $this->addRowAction('view');
        $this->addRowAction('edit');
        $this->addRowAction('delete');

    		parent::__construct();

        $this->bootstrap = true;
        $this->_path = __PS_BASE_URI__.'modules/'.$this->module->name.'/';


        $this->fields_list = array(
      			'id_faq' => array(
        				'title' => $this->trans('ID'),
        				'align' => 'text-center',
                'class' => 'fixed-width-xs',
      			),

      			'title' => array(
        				'title' => $this->trans('Title'),
        				'maxlength' => 100,
      			),
      			'active' => array(
        				'title' => $this->trans('Active'),
        				'active' => 'status',
        				'align' => 'center',
        				'type' => 'bool',
        				'width' => 70,
        				'orderby' => false
      			)
    		);

        $this->bulk_actions = array('delete' => array('text' => $this->trans('Delete selected'), 'confirm' => $this->trans('Delete selected items?')));
	  }

    public function renderForm()
    {
        $form_inputs = array();

        $form_inputs = array_merge($form_inputs, array(

            array(
                'type'      => 'text',
                'label'     => $this->trans('Title', array(), 'Admin.Fusion.StoreFaqs'),
                'name'      => 'title',
                'col'       => 8,
                'required'  => true,
                'lang'      => true
            ),
            array(
                'type'      => 'textarea',
                'label'     => $this->trans('Description', array(), 'Admin.Fusion.StoreFaqs'),
                'name'      => 'description',
                'lang'      => true,
                'required'  => true,
                'col'       => 8,
                'rows'      => 10,
                'autoload_rte' => true,
            ),
            array(
                'type' => 'switch',
                'label' => $this->trans('Active', array(), 'Admin.Fusion.StoreFaqs'),
                'name' => 'active',
                'values' => [
                    [
                        'id' => 'active_on',
                        'value' => 1,
                        'label' => $this->trans('Yes', [], 'Admin.Global'),
                    ],
                    [
                        'id' => 'active_off',
                        'value' => 0,
                        'label' => $this->trans('No', [], 'Admin.Global'),
                    ],
                ]
            ),
        ));

        $this->fields_form = array(
            'legend' => array(
                'title' => $this->trans('Faq', array(), 'Admin.Fusion.StoreFaqs'),
                'icon' => '',
            ),
            'input' => $form_inputs,
            'submit' => array(
                'title' => $this->trans('Save', array(), 'Admin.Global'),
            ),
        );

        return parent::renderForm();
    }










  	public function setMedia($isNewTheme = false)
    {
        parent::setMedia($isNewTheme);
    }

    public function postProcess()
    {
        return parent::postProcess(true);
    }

}
?>